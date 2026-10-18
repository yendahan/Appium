"""pytest wiring: CLI options, driver fixture, screenshots/diagnostics and Zephyr publishing."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, Optional

import pytest

from framework import driver_factory, zephyr_reporter
from framework.config_manager import ConfigManager
from framework.mobile_actions import MobileActions

LOG = logging.getLogger("conftest")
SCREENSHOT_KEY = "screenshot_path"


def pytest_addoption(parser: pytest.Parser) -> None:
    group = parser.getgroup("appium")
    group.addoption("--env", default=None, help="environment profile (default: qa; env var ENV)")
    group.addoption("--device", default=None, help="device profile (default: emulator; env var DEVICE)")
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


@pytest.fixture
def driver(request: pytest.FixtureRequest):
    """A fresh Appium session per test (same as the Java BaseTest @BeforeMethod/@AfterMethod)."""
    LOG.info("=== START %s ===", request.node.nodeid)
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
    if report.when == "call" or (report.when == "setup" and not report.passed):
        drv = item.funcargs.get("driver") if hasattr(item, "funcargs") else None
        screenshot: Optional[Path] = None
        if drv is not None and report.when == "call":
            screenshot = _capture(item, drv, report.passed)
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
    marker = item.get_closest_marker("zephyr")
    if marker is None or not marker.args:
        return
    if report.passed:
        status, error = "Pass", None
    elif report.skipped:
        status, error = "Blocked", None
    else:
        status = "Fail"
        error = repr(call.excinfo.value) if call.excinfo else "setup failed"
    zephyr_reporter.publish(marker.args[0], status, error, screenshot)
