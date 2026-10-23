"""pytest wiring: CLI options, driver fixture, screenshots/diagnostics and Zephyr publishing."""
from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Dict, Optional

import pytest

from framework import driver_factory, mobile_actions, zephyr_cases, zephyr_reporter
from framework.config_manager import ConfigManager
from framework.mobile_actions import MobileActions
from framework.shared_session import SharedSession
from pages.home_page import HomePage

LOG = logging.getLogger("conftest")
SCREENSHOT_KEY = "screenshot_path"


def pytest_addoption(parser: pytest.Parser) -> None:
    group = parser.getgroup("appium")
    group.addoption("--env", default=None, help="environment profile (default: qa; env var ENV)")
    group.addoption("--device", default=None, help="device profile (default: emulator; env var DEVICE)")
    group.addoption("--reuse-app", action="store_true", default=os.environ.get("REUSE_APP", "").lower() == "true",
                    help="tests marked shared_session keep one logged-in app session instead of a fresh one each")
    group.addoption("--cfg", action="append", default=[], metavar="KEY=VALUE",
                    help="override any config key, e.g. --cfg appium.url=http://10.0.0.5:4723")


def pytest_configure(config: pytest.Config) -> None:
    overrides: Dict[str, str] = {}
    for item in config.getoption("--cfg"):
        key, sep, value = item.partition("=")
        if not sep:
            raise pytest.UsageError(f"--cfg expects KEY=VALUE but got '{item}'")
        overrides[key.strip()] = value
    ConfigManager.configure(config.getoption("--env"), config.getoption("--device"), overrides)


def pytest_collection_finish(session: pytest.Session) -> None:
    """Checks the Zephyr setup once the final test selection is known, before any test runs."""
    if not any(item.get_closest_marker("zephyr") for item in session.items):
        return
    try:
        zephyr_reporter.start_run()
    except zephyr_reporter.ZephyrSetupError as e:
        pytest.exit(f"Zephyr setup error, no test was run: {e}", returncode=2)


@pytest.fixture(autouse=True)
def _screenshot_folder(request: pytest.FixtureRequest):
    """Screenshots of a test go in the folders its file sits in under tests/ (like its Zephyr folder)."""
    mobile_actions.set_screenshot_subfolder(zephyr_cases.folder_of(request.node.nodeid))
    yield
    mobile_actions.set_screenshot_subfolder("")


SHARED = SharedSession(lambda: driver_factory.create(ConfigManager.get_instance()),
                       lambda drv: HomePage(drv).return_to_home())


def pytest_sessionfinish(session: pytest.Session) -> None:
    SHARED.discard()


@pytest.fixture
def driver(request: pytest.FixtureRequest):
    """A fresh Appium session per test (same as the Java BaseTest @BeforeMethod/@AfterMethod).

    With --reuse-app, a test marked shared_session reuses the open session of its account instead."""
    LOG.info("=== START %s ===", request.node.nodeid)
    shared = request.node.get_closest_marker("shared_session")
    if shared and request.config.getoption("--reuse-app"):
        drv = SHARED.acquire(shared.args[0])
        drv.reused_session = True
        yield drv
        LOG.info("=== END %s ===", request.node.nodeid)
        if getattr(request.node, "failed_phase", False):
            SHARED.discard()  # a failure can leave any screen open: the next test starts fresh
        return
    drv = driver_factory.create(ConfigManager.get_instance())
    yield drv
    LOG.info("=== END %s ===", request.node.nodeid)
    try:
        drv.quit()
    except Exception as e:  # noqa: BLE001
        LOG.warning("driver.quit() failed: %s", e)


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item: pytest.Item, call: pytest.CallInfo):
    outcome = yield
    report = outcome.get_result()
    if report.failed:
        item.failed_phase = True
    if report.when == "call" or (report.when == "setup" and not report.passed):
        drv = item.funcargs.get("driver") if hasattr(item, "funcargs") else None
        screenshot: Optional[Path] = None
        if drv is not None and (report.when == "call" or report.failed):
            screenshot = _capture(item, drv, report.passed)  # a failed login in a fixture is a setup failure
        _publish_to_zephyr(item, report, call, screenshot)


def _capture(item: pytest.Item, drv, passed: bool) -> Optional[Path]:
    name = item.nodeid.split("::", 1)[-1].replace("::", ".")
    actions = MobileActions(drv)
    shot: Optional[Path] = None
    try:
        shot = actions.screenshot(name, "PASSED" if passed else "FAILED")
    except Exception as e:  # noqa: BLE001
        LOG.warning("Could not capture screenshot: %s", e)
    if not passed:
        art = Path(ConfigManager.get_instance().require("artifacts.dir")) / "diagnostics"
        try:
            art.mkdir(parents=True, exist_ok=True)
            (art / f"{_safe(name)}-pagesource.xml").write_text(actions.page_source(), encoding="utf-8")
        except Exception as e:  # noqa: BLE001
            LOG.warning("Could not capture page source: %s", e)
        try:
            lines = [str(e) for e in drv.get_log("logcat")]
            (art / f"{_safe(name)}-logcat.txt").write_text("\n".join(lines), encoding="utf-8")
        except Exception as e:  # noqa: BLE001
            LOG.warning("Could not capture logcat: %s", e)
    return shot


def _safe(name: str) -> str:
    from framework.mobile_actions import sanitize
    return sanitize(name)


def _publish_to_zephyr(item: pytest.Item, report: pytest.TestReport, call: pytest.CallInfo,
                       screenshot: Optional[Path]) -> None:
    if item.get_closest_marker("zephyr") is None:
        return
    case_key = zephyr_reporter.resolve(item.nodeid)
    if case_key is None:
        LOG.warning("Zephyr: no case found for %s in this run's folder, result not reported", item.nodeid)
        return
    if report.passed:
        status, error = "Pass", None
    elif report.skipped:
        status, error = "Blocked", None
    else:
        status = "Fail"
        error = repr(call.excinfo.value) if call.excinfo else "setup failed"
    zephyr_reporter.publish(case_key, status, error, screenshot)


def pytest_terminal_summary(terminalreporter) -> None:
    """After the run: what was created in Zephyr and where the results went."""
    line = zephyr_reporter.summary()
    if line:
        terminalreporter.write_sep("-", "Zephyr")
        terminalreporter.write_line(line)
