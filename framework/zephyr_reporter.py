"""Publishes results of tests marked ``@pytest.mark.zephyr`` to a Zephyr Scale cycle.

Inactive unless env var ZEPHYR_TOKEN and ``zephyr.project.key`` are set. Publishing a result that fails is only
logged and never changes a test result. Setting up the run is different: a missing cycle name or case-folder
setting, or a failure creating the folder, its cases or the cycle, stops the run before any test starts
(``start_run`` raises ``ZephyrSetupError`` with the reason). Every run creates a new cycle; the case folder is created
if it does not exist, and any case defined in ``zephyr_cases.CASES`` that the folder lacks is created in it. A test
reports only to the case with its name in that folder.
"""
from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from collections import Counter
from typing import Dict, List, Optional, Tuple

from framework import zephyr_cases
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
# Case name -> key of the cases in this run's folder; tests are linked to their case by name.
_case_keys_by_name: Dict[str, str] = {}
# What this run set up and published, for the end-of-run summary.
_info: Dict[str, object] = {}
_results: Counter = Counter()


def escape_html(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def publish(case_key: str, status: str, error: Optional[str], screenshot: Optional[Path]) -> None:
    """status: Pass | Fail | Blocked."""
    if not _init():
        return
    comment = f"Actual: {error}" if error else None
    note = _screenshot_note(screenshot) if screenshot else None
    try:
        exec_key = _executions.get(case_key)
        if exec_key:
            _client.update_execution(exec_key, status, comment)
        else:
            exec_key = _client.post_execution(_cycle_key, case_key, status, comment)
            _executions[case_key] = exec_key
        LOG.info("Zephyr: %s -> %s in %s", case_key, status, _cycle_key)
        _results[status] += 1
        try:
            expected = [(st.get("inline") or {}).get("expectedResult") or "" for st in _client.execution_steps(exec_key)]
            _client.set_step_results(exec_key, step_results(expected, status, error, note))
        except Exception as e:  # noqa: BLE001
            LOG.warning("Zephyr: could not update step results for %s: %s", exec_key, e)
    except Exception as e:  # noqa: BLE001
        LOG.warning("Zephyr: could not publish %s: %s", case_key, e)


def step_results(expected: List[str], status: str, error: Optional[str], note: Optional[str]) -> List[Dict[str, str]]:
    """Status and actual result for each step, given each step's expected result.

    Pass: every step passed, and its actual result is what the step expected (so each step reads differently).
    Fail / Blocked: the failure text is found in the step it belongs to (see zephyr_cases.failing_step), steps before
    it passed, steps after it were not executed; a failure that can't be placed goes on the last step.
    The note (e.g. the screenshot link) is added to the failing step, or to the last step on a pass.
    """
    count = len(expected)
    if count == 0:
        return []
    if status == "Pass":
        items = [{"statusName": "Pass", "actualResult": escape_html(e) if e else "As expected"} for e in expected]
        failing = count - 1
    elif error is None:  # skipped (Blocked) without a failure: nothing ran
        items = [{"statusName": status, "actualResult": "Test was skipped"} for _ in expected]
        failing = count - 1
    else:
        found = zephyr_cases.failing_step(error, expected)
        failing = count - 1 if found is None else found
        items = []
        for i, e in enumerate(expected):
            if i < failing:
                items.append({"statusName": "Pass", "actualResult": escape_html(e) if e else "As expected"})
            elif i == failing:
                items.append({"statusName": status, "actualResult": escape_html(error)})
            else:
                items.append({"statusName": "Not Executed", "actualResult": "Not executed: an earlier step failed"})
    if note:
        items[failing]["actualResult"] += f"<br>{note}"
    return items


def _screenshot_note(png: Path) -> str:
    cfg = ConfigManager.get_instance()
    rel = png.name
    try:
        base = Path(cfg.require("artifacts.dir")).resolve() / "Screenshots"
        rel = str(png.resolve().relative_to(base))
    except Exception as e:  # noqa: BLE001
        LOG.warning("Zephyr: could not shorten screenshot path %s: %s", png, e)
    link = cfg.get("zephyr.artifacts.link")
    if not link:
        return f"Screenshot: {escape_html(rel)}"
    return f'Screenshot: <a href="{link.replace(chr(34), "&quot;")}">OneDrive folder</a> &gt; {escape_html(rel)}'


class ZephyrSetupError(Exception):
    """The Zephyr settings for this run are missing or wrong; the run must not start."""


def cycle_name(cfg: ConfigManager, stamp: str) -> str:
    """Name of this run's new cycle: ZEPHYR_CYCLE_NAME followed by the date and time."""
    return f"{cfg.get('zephyr.cycle.name')} {stamp}"


def _prepare_cycle(client: ZephyrClient, case_keys: List[str]) -> None:
    """Lists every case of the run's folder as Not Executed so skipped (e.g. risky) tests still appear."""
    _executions.update(client.latest_executions(_cycle_key))
    for case_key in case_keys:
        exec_key = _executions.get(case_key)
        if exec_key is None:
            _executions[case_key] = client.post_execution(_cycle_key, case_key, "Not Executed", None)
        else:
            client.update_execution(exec_key, "Not Executed", None)


class _ReusePool:
    """Existing cases to reuse (in no folder first, then in other folders), looked up once, only if something is
    missing, and handed out by name."""

    def __init__(self, client: ZephyrClient) -> None:
        self._client = client
        self._by_name: Optional[Dict[str, List[str]]] = None

    def take(self, name: str) -> Optional[str]:
        if self._by_name is None:
            try:
                self._by_name = self._client.reusable_cases()
            except Exception as e:  # noqa: BLE001
                LOG.warning("Zephyr: could not look for existing cases to reuse, creating new ones: %s", e)
                self._by_name = {}
        keys = self._by_name.get(name)
        return keys.pop(0) if keys else None


def _tidy_upper_folders(client: ZephyrClient, leaf: str, wanted: List[zephyr_cases.Case],
                       existing: Dict[str, str]) -> Tuple[Dict[str, str], int]:
    """Makes the innermost folder the only one holding the defined cases.

    In every upper folder of the tree (e.g. <top> and <top>/Android), a case with a defined name is moved down into
    the innermost folder if that lacks it, otherwise it is a duplicate and is taken out of the folder tree (not
    deleted). Other cases are left alone. Returns (name -> key of the cases pulled down, number of duplicates moved
    out); failures are logged and skipped.
    """
    names = {c.name for c in wanted}
    parts = [p.strip() for p in leaf.split("/") if p.strip()]
    have = dict(existing)
    pulled: Dict[str, str] = {}
    moved_out = 0
    for i in range(1, len(parts)):
        upper = "/".join(parts[:i])
        try:
            listing = client.list_cases(upper)
        except Exception as e:  # noqa: BLE001
            LOG.warning("Zephyr: could not read upper folder '%s': %s", upper, e)
            continue
        for name, key in listing or []:
            if name not in names:
                continue
            try:
                if name in have:
                    client.unfile_case(key)
                    moved_out += 1
                    LOG.info("Zephyr: duplicate %s ('%s') taken out of '%s'", key, name, upper)
                else:
                    client.move_case(key, leaf)
                    have[name] = pulled[name] = key
                    LOG.info("Zephyr: %s ('%s') moved from '%s' down into '%s'", key, name, upper, leaf)
            except Exception as e:  # noqa: BLE001
                LOG.warning("Zephyr: could not tidy case %s in '%s': %s", key, upper, e)
    return pulled, moved_out


def _ensure_cases(client: ZephyrClient, folder: str, wanted: List[zephyr_cases.Case], existing: Dict[str, str],
                  pool: _ReusePool) -> Tuple[Dict[str, str], Dict[str, str]]:
    """Gets every wanted case it does not have yet (by name) into the folder.

    An existing case with that name (in no folder first, otherwise in another folder) is moved in; if there is
    none (or moving it fails) a new case is created. Returns (moved, created) as name -> key. Raises ZephyrSetupError naming the case that failed.
    """
    missing = [c for c in wanted if c.name not in existing]
    moved: Dict[str, str] = {}
    created: Dict[str, str] = {}
    for case in missing:
        key = pool.take(case.name)
        if key:
            try:
                client.move_case(key, folder)
                moved[case.name] = key
                continue
            except Exception as e:  # noqa: BLE001
                LOG.warning("Zephyr: could not move existing case %s into '%s', creating a new one: %s", key, folder, e)
        try:
            new_key, _ = client.create_case(case.name, folder, case.objective, case.steps)
        except Exception as e:  # noqa: BLE001
            raise ZephyrSetupError(f"could not create test case '{case.name}' in folder '{folder}': {e}") from e
        created[case.name] = new_key
    if missing:
        LOG.info("Zephyr: folder '%s' needed %d cases: %d moved in from existing cases, %d created",
                 folder, len(missing), len(moved), len(created))
    return moved, created


def resolve(nodeid: str) -> Optional[str]:
    """Key of the case a test reports to: the case with the test's registry name in this run's folder, or None."""
    case = zephyr_cases.case_for(nodeid)
    return _case_keys_by_name.get(case.name) if case else None


def _tidy_text() -> str:
    parts = []
    if _info.get("pulled"):
        parts.append(f"{_info['pulled']} pulled down from upper folders")
    if _info.get("moved_out"):
        parts.append(f"{_info['moved_out']} duplicates taken out of upper folders")
    return (", " + ", ".join(parts)) if parts else ""


def summary() -> Optional[str]:
    """One line saying what this run created in Zephyr and where the results went; None when Zephyr was not used."""
    if _client is None or not _info:
        return None
    folder = f"folder '{_info['folder']}' ({'created' if _info['folder_created'] else 'existing'}, " \
             f"{_info['cases']} cases: {_info['cases_moved']} moved in from existing, {_info['cases_created']} created" \
             f"{_tidy_text()})"
    results = ", ".join(f"{n} {status}" for status, n in sorted(_results.items())) or "no results"
    return f"Zephyr: {folder} | cycle {_info['cycle_key']} '{_info['cycle_name']}' | results: {results}"


def start_run(client: Optional[ZephyrClient] = None, now: Optional[datetime] = None) -> None:
    """Sets up this run's Zephyr cycle and case folder once, before any test runs.

    Raises ZephyrSetupError (so the run stops) when no cycle name or no case folder is set, or when creating the
    folder, its cases or the cycle fails (the message says which step and why). Does nothing when Zephyr is not
    configured (no token).
    """
    global _client, _cycle_key, _initialised
    if _initialised:
        return
    cfg = ConfigManager.get_instance()
    token = os.environ.get("ZEPHYR_TOKEN", "").strip()
    if not token or not cfg.has("zephyr.project.key"):
        _initialised = True
        return
    if not cfg.has("zephyr.cycle.name"):
        raise ZephyrSetupError("ZEPHYR_CYCLE_NAME is not set: give the Zephyr test cycle a name for this run")
    folder = cfg.get("zephyr.cases.folder")
    if not folder:
        raise ZephyrSetupError("ZEPHYR_CASES_FOLDER is not set: name the Zephyr test-case folder for this run")
    if cfg.has("zephyr.cycle.key"):
        LOG.warning("Zephyr: ZEPHYR_CYCLE_KEY is ignored: every run creates a new cycle")
    client = client or ZephyrClient(cfg.get("zephyr.base.url") or DEFAULT_URL, token, cfg.get("zephyr.project.key"))
    top = folder
    step, new_folders, leaves = f"reading folder '{top}'", [], []
    cases: Dict[str, str] = {}
    created_total = moved_total = pulled_total = moved_out_total = 0
    pool = _ReusePool(client)
    try:
        # The run's folder is the top; below it the project's folders under tests/ (e.g. Android/Upgraded Consumer
        # Account) are mirrored, and each test's case lives in the folder its test file sits in.
        for sub, wanted in zephyr_cases.groups().items():
            leaf = f"{top}/{sub}" if sub else top
            leaves.append(leaf)
            step = f"reading folder '{leaf}'"
            existing = client.cases_in_folder(leaf)
            if existing is None:
                step = f"creating folder '{leaf}'"
                client.create_folder(leaf)
                new_folders.append(leaf)
                LOG.info("Zephyr: created test-case folder '%s'", leaf)
                existing = {}
            step = f"tidying the upper folders of '{leaf}'"
            pulled, moved_out = _tidy_upper_folders(client, leaf, wanted, existing)
            existing = {**existing, **pulled}
            pulled_total += len(pulled)
            moved_out_total += moved_out
            step = f"creating the test cases in folder '{leaf}'"
            moved, created = _ensure_cases(client, leaf, wanted, existing, pool)
            moved_total += len(moved)
            created_total += len(created)
            # no re-listing: Zephyr's listing can lag behind what was just created or moved
            cases.update({**existing, **moved, **created})
        _case_keys_by_name.update(cases)
        step = "creating the cycle"
        name = cycle_name(cfg, (now or datetime.now()).strftime("%Y-%m-%d %H:%M"))
        _cycle_key = client.create_cycle(name)
        LOG.info("Zephyr: created cycle %s '%s'", _cycle_key, name)
        step = "listing the cases in the cycle"
        _prepare_cycle(client, list(cases.values()))
        LOG.info("Zephyr: cycle %s lists %d cases from folder '%s'", _cycle_key, len(_executions), ", ".join(leaves))
        _info.update(folder=", ".join(leaves), folder_created=bool(new_folders), cases_created=created_total,
                     cases_moved=moved_total, pulled=pulled_total, moved_out=moved_out_total,
                     cases=len(cases), cycle_key=_cycle_key, cycle_name=name)
    except Exception as e:  # noqa: BLE001
        note = f" The folder(s) {', '.join(repr(f) for f in new_folders)} were created; run again to fill them." \
            if new_folders else ""
        reason = str(e) if isinstance(e, ZephyrSetupError) else f"Zephyr setup failed while {step}: {e}"
        raise ZephyrSetupError(f"{reason}.{note} To run without Zephyr, unset ZEPHYR_TOKEN.") from e
    _client = client
    _initialised = True


def _init() -> bool:
    """Lazy fallback: set up on the first result if start_run was not called (a bad setup then only disables)."""
    global _initialised
    if not _initialised:
        try:
            start_run()
        except ZephyrSetupError as e:
            LOG.error("Zephyr disabled for this run: %s", e)
            _initialised = True
    return _client is not None
