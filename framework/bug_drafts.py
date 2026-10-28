"""One bug-report draft per failed test of a run, ready to be filed in Jira (Claude files them on request, nothing is created automatically).

Written next to the HTML report: <artifacts.dir>/Reports/<run folder>/bugs/BUG-<nn>-<test>.md plus a bugs.json index. Only test ids, scenario text,
error text, file paths and screen messages go in: credentials and mobile numbers are never read.
"""
from __future__ import annotations

import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Sequence

from framework import zephyr_cases
from framework.mobile_actions import sanitize
from framework.run_report import TestResult

LOG = logging.getLogger(__name__)

# (text on screen, suggested cause, what the screen says in plain words); the first match in the saved page source wins.
SCREEN_MESSAGES = [
    ("No Connection Found", "Environment (network)", "The app shows \"No Connection Found!\" (emulator or staging network drop)."),
    ("check if you are connected to the internet", "Environment (network)", "The app shows an Oops popup asking to check the internet connection."),
    ("blocked temporarily", "Test account locked", "The app shows \"This account has been blocked temporarily\" (earlier wrong-password attempts)."),
    ("no longer accept additional funds", "Test data / state", "The app shows \"The account you entered can no longer accept additional funds\" (recipient wallet at its limit)."),
    ("Insufficient Funds", "Test data / state", "The app shows the Insufficient Funds popup (the wallet balance is below the amount)."),
    ("above your wallet limit", "Test data / state", "The app shows \"Amount is above your wallet limit. Upgrade your account\"."),
    ("verification code we sent", "Needs triage (possible app defect)", "The app asks for a 6-digit verification code (OTP)."),
]
HIGH_SEVERITY_WORDS = ("send_money", "payments", "pay_", "add_money", "withdraw", "otp", "bills")


def screen_message(page_source: str) -> Optional[tuple]:
    for text, cause, plain in SCREEN_MESSAGES:
        if text.lower() in (page_source or "").lower():
            return cause, plain
    return None


def severity(result: TestResult) -> str:
    return "High" if any(w in result.nodeid.lower() for w in HIGH_SEVERITY_WORDS) else "Medium"


def expected_text(result: TestResult) -> str:
    steps = list(result.steps or [])
    if steps:
        index = zephyr_cases.failing_step(result.error_text or result.error, [e for _, e in steps])
        if index is not None:
            return steps[index][1]
        return steps[-1][1]
    return result.objective or result.doc or "The scenario completes as described."


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def _evidence(result: TestResult, artifacts_dir: Path, run_folder: str) -> List[str]:
    lines: List[str] = []
    if result.screenshot:
        lines.append(f"Failure screenshot: {result.screenshot}")
        run_dir = Path(result.screenshot).parent.parent
        for sub, label in (("RECEIPT", "Receipt screenshots"), ("VIDEO", "Screen recordings")):
            if (run_dir / sub).is_dir():
                lines.append(f"{label} of the run: {run_dir / sub}")
    page = artifacts_dir / "diagnostics" / f"{sanitize(result.nodeid.split('::', 1)[-1].replace('::', '.'))}-pagesource.xml"
    if page.is_file():
        lines.append(f"Page source at the failure: {page}")
    return lines


def draft(result: TestResult, number: int, artifacts_dir: Path, run_folder: str, env: Dict[str, str]) -> Dict[str, object]:
    page = artifacts_dir / "diagnostics" / f"{sanitize(result.nodeid.split('::', 1)[-1].replace('::', '.'))}-pagesource.xml"
    screen = screen_message(_read(page))
    cause = screen[0] if screen else "Needs triage (possible app defect)"
    actual = result.error or "The test failed."
    if screen:
        actual = f"{screen[1]} Test error: {actual}"
    steps = [f"{i}. {a}" for i, (a, _) in enumerate(result.steps or [], start=1)]
    if not steps and result.doc:
        steps = [result.doc]
    return {
        "number": number,
        "summary": result.name if result.name.lower().startswith(result.folder.lower()) else f"{result.folder}: {result.name}",
        "severity": severity(result),
        "suggested_cause": cause,
        "environment": env,
        "test": result.nodeid,
        "steps": steps,
        "expected": expected_text(result),
        "actual": actual,
        "evidence": _evidence(result, artifacts_dir, run_folder),
    }


def _markdown(d: Dict[str, object]) -> str:
    env = "\n".join(f"- {k}: {v}" for k, v in d["environment"].items())
    steps = "\n".join(d["steps"]) or "See the test."
    evidence = "\n".join(f"- {e}" for e in d["evidence"]) or "- none saved"
    return (f"# {d['summary']}\n\n**Severity (suggested):** {d['severity']}  \n**Suggested cause:** {d['suggested_cause']}  \n"
            f"**Test:** {d['test']}\n\n## Environment\n{env}\n\n## Steps to reproduce\n{steps}\n\n## Expected result\n{d['expected']}\n\n"
            f"## Actual result\n{d['actual']}\n\n## Evidence\n{evidence}\n")


def write(results: Sequence[TestResult], artifacts_dir: Path, run_folder: str, env: Dict[str, str]) -> Optional[Path]:
    """Writes the drafts of the failed tests; returns the folder, or None when nothing failed."""
    failed = [r for r in results if r.outcome == "failed"]
    if not failed:
        return None
    artifacts_dir = Path(artifacts_dir)
    target = artifacts_dir / "Reports" / run_folder / "bugs"
    target.mkdir(parents=True, exist_ok=True)
    env = dict(env)
    env.setdefault("run", _run_label(run_folder))
    drafts = [draft(r, i, artifacts_dir, run_folder, env) for i, r in enumerate(failed, start=1)]
    for d in drafts:
        name = re.sub(r"[^A-Za-z0-9._-]+", "_", str(d["test"]).split("::", 1)[-1])[:80]
        (target / f"BUG-{d['number']:02d}-{name}.md").write_text(_markdown(d), encoding="utf-8")
    (target / "bugs.json").write_text(json.dumps(drafts, indent=2), encoding="utf-8")
    return target


def _run_label(run_folder: str) -> str:
    try:
        return datetime.strptime(run_folder, "%Y-%m-%d_%H-%M-%S").strftime("%Y-%m-%d %H:%M")
    except ValueError:
        return run_folder
