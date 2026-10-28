import json
import os
from pathlib import Path

import pytest

from framework import bug_drafts
from framework.run_report import TestResult

pytestmark = pytest.mark.unit

RUN = "2026-10-27_18-43-01"


def make(tmp_path: Path, screen_text: str = "No Connection Found!"):
    shot = tmp_path / "Screenshots" / "Android" / "Upgraded" / RUN / "FAILED" / "test_x.png"
    shot.parent.mkdir(parents=True)
    shot.write_bytes(b"png")
    (tmp_path / "Screenshots" / "Android" / "Upgraded" / RUN / "VIDEO").mkdir()
    diag = tmp_path / "diagnostics"
    diag.mkdir()
    (diag / "test_wallet_to_other_bank_valid-pagesource.xml").write_text(f'<node content-desc="{screen_text}"/>', encoding="utf-8")
    failed = TestResult("Upgraded Consumer Account/test_payments.py::test_wallet_to_other_bank_valid", "Upgraded Consumer Account",
                        "Send Money from Wallet: To Other Banks accepts a valid account", "failed",
                        error="Element not clickable within 30s: ('accessibility id', 'NEXT')",
                        error_text="framework.exceptions.FrameworkException: Element not clickable within 30s: NEXT",
                        screenshot=shot,
                        steps=[("Open Send Money from the Wallet tab", "The review step is displayed"),
                               ("Tap CONFIRM", "The receipt shows 'Successfully Sent!'")])
    passed = TestResult("Basic Account/test_a.py::test_ok", "Basic Account", "ok", "passed")
    return [failed, passed]


def test_one_draft_per_failed_test_with_the_fields(tmp_path):
    folder = bug_drafts.write(make(tmp_path), tmp_path, RUN, {"app": "com.bayad", "env": "qa", "device": "emulator"})
    assert folder == tmp_path / "Reports" / RUN / "bugs"
    files = sorted(p.name for p in folder.glob("BUG-*.md"))
    assert len(files) == 1 and files[0].startswith("BUG-01-")
    text = (folder / files[0]).read_text(encoding="utf-8")
    assert "# Upgraded Consumer Account: Send Money from Wallet: To Other Banks accepts a valid account" in text
    assert "**Severity (suggested):** High" in text
    assert "**Suggested cause:** Environment (network)" in text
    assert "1. Open Send Money from the Wallet tab" in text and "2. Tap CONFIRM" in text
    assert "No Connection Found" in text and "Element not clickable" in text
    assert "- app: com.bayad" in text and "Screen recordings of the run:" in text and "Page source at the failure:" in text
    index = json.loads((folder / "bugs.json").read_text(encoding="utf-8"))
    assert len(index) == 1 and index[0]["suggested_cause"] == "Environment (network)"


def test_unknown_screen_needs_triage_and_expected_is_the_last_step(tmp_path):
    folder = bug_drafts.write(make(tmp_path, "Something else"), tmp_path, RUN, {"env": "qa"})
    d = json.loads((folder / "bugs.json").read_text(encoding="utf-8"))[0]
    assert d["suggested_cause"] == "Needs triage (possible app defect)"
    assert d["expected"] == "The receipt shows 'Successfully Sent!'"


def test_nothing_failed_writes_nothing(tmp_path):
    assert bug_drafts.write([TestResult("a::b", "F", "n", "passed")], tmp_path, RUN, {}) is None
    assert not (tmp_path / "Reports").exists()


def test_environment_secrets_never_appear(tmp_path, monkeypatch):
    monkeypatch.setenv("TEST_PASSWORD", "Sup3r-Secret-Pw")
    folder = bug_drafts.write(make(tmp_path), tmp_path, RUN, {"env": "qa"})
    assert all("Sup3r-Secret-Pw" not in p.read_text(encoding="utf-8") for p in folder.iterdir())
