"""Publishes results of tests marked ``@pytest.mark.zephyr("AMW-T123")`` to a Zephyr Scale cycle.

Inactive unless env var ZEPHYR_TOKEN and ``zephyr.project.key`` are set. Errors are only logged so
Jira problems never change a test result.
"""
from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

from framework.config_manager import ConfigManager
from framework.zephyr_client import ZephyrClient

import os

LOG = logging.getLogger(__name__)
DEFAULT_URL = "https://api.zephyrscale.smartbear.com/v2"

_client: Optional[ZephyrClient] = None
_cycle_key: Optional[str] = None
_initialised = False
# Case key -> execution key in the current cycle; lets a result update the pre-created row.
_executions: Dict[str, str] = {}


def escape_html(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def publish(case_key: str, status: str, error: Optional[str], screenshot: Optional[Path]) -> None:
    """status: Pass | Fail | Blocked."""
    if not _init():
        return
    comment = f"Actual: {error}" if error else None
    actual = escape_html(error) if error else "As expected"
    note = _screenshot_note(screenshot) if screenshot else None
    try:
        exec_key = _executions.get(case_key)
        if exec_key:
            _client.update_execution(exec_key, status, comment)
        else:
            exec_key = _client.post_execution(_cycle_key, case_key, status, comment)
            _executions[case_key] = exec_key
        LOG.info("Zephyr: %s -> %s in %s", case_key, status, _cycle_key)
        try:
            _client.update_step_results(exec_key, status, actual, note)
        except Exception as e:  # noqa: BLE001
            LOG.warning("Zephyr: could not update step results for %s: %s", exec_key, e)
    except Exception as e:  # noqa: BLE001
        LOG.warning("Zephyr: could not publish %s: %s", case_key, e)


def _screenshot_note(png: Path) -> str:
    cfg = ConfigManager.get_instance()
    rel = png.name
    try:
        base = Path(cfg.require("artifacts.dir")).resolve() / "screenshots"
        rel = str(png.resolve().relative_to(base))
    except Exception as e:  # noqa: BLE001
        LOG.warning("Zephyr: could not shorten screenshot path %s: %s", png, e)
    link = cfg.get("zephyr.artifacts.link")
    if not link:
        return f"Screenshot: {escape_html(rel)}"
    return f'Screenshot: <a href="{link.replace(chr(34), "&quot;")}">OneDrive folder</a> &gt; {escape_html(rel)}'


def _prepare_cycle(client: ZephyrClient, cfg: ConfigManager) -> None:
    """Lists every case of the configured folder as Not Executed so skipped (e.g. risky) tests still appear."""
    try:
        folder = cfg.get("zephyr.cases.folder") or "Mobile Automation"
        _executions.update(client.latest_executions(_cycle_key))
        for case_key in client.case_keys_in_folder(folder):
            exec_key = _executions.get(case_key)
            if exec_key is None:
                _executions[case_key] = client.post_execution(_cycle_key, case_key, "Not Executed", None)
            else:
                client.update_execution(exec_key, "Not Executed", None)
        LOG.info("Zephyr: cycle %s lists %d cases", _cycle_key, len(_executions))
    except Exception as e:  # noqa: BLE001
        LOG.warning("Zephyr: could not pre-fill cycle %s: %s", _cycle_key, e)


def _init() -> bool:
    global _client, _cycle_key, _initialised
    if _initialised:
        return _client is not None
    _initialised = True
    cfg = ConfigManager.get_instance()
    token = os.environ.get("ZEPHYR_TOKEN", "").strip()
    if not token or not cfg.has("zephyr.project.key"):
        return False
    try:
        client = ZephyrClient(cfg.get("zephyr.base.url") or DEFAULT_URL, token, cfg.get("zephyr.project.key"))
        reuse = os.environ.get("ZEPHYR_CYCLE_KEY", "").strip() or cfg.get("zephyr.cycle.key")
        if reuse:
            _cycle_key = reuse
            LOG.info("Zephyr: reusing cycle %s", _cycle_key)
        else:
            stamp = datetime.now().strftime("%Y-%m-%d %H:%M")
            _cycle_key = client.create_cycle(f"Automation {cfg.env}/{cfg.device} {stamp}")
            LOG.info("Zephyr: created cycle %s", _cycle_key)
        _client = client
        _prepare_cycle(client, cfg)
        return True
    except Exception as e:  # noqa: BLE001
        LOG.warning("Zephyr disabled for this run: %s", e)
        return False
