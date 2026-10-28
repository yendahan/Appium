from pathlib import Path

import pytest

from framework import run_report
from framework.run_report import TestResult

pytestmark = pytest.mark.unit


def make(tmp_path: Path):
    shot = tmp_path / "shot.png"
    try:
        from PIL import Image
        Image.new("RGB", (200, 400), "white").save(shot)
    except ImportError:
        shot.write_bytes(b"not an image")
    return [
        TestResult("Basic Account/test_a.py::test_ok", "Basic Account", "Basic: ok <b>", "passed", doc="Checks it works",
                   screenshot=shot, steps=[("Tap Go", "Home shows")], objective="Positive"),
        TestResult("Basic Account/test_a.py::test_bad", "Basic Account", "Basic: bad", "failed",
                   error="Element not clickable within 30s: ('accessibility id', 'NEXT')", screenshot=None),
        TestResult("Upgraded/test_b.py::test_skip", "Upgraded", "skipped one", "skipped"),
    ]


def test_report_has_totals_folders_and_scenarios(tmp_path):
    path = run_report.build(make(tmp_path), tmp_path, "2026-10-27_18-43-01")
    text = path.read_text(encoding="utf-8")
    assert path == tmp_path / "Reports" / "2026-10-27_18-43-01.html"
    assert '<div class="big ok">1<small>passed</small>' in text and '<div class="big bad">1<small>failed</small>' in text
    assert "Basic Account" in text and "Upgraded" in text
    assert "Tap Go" in text and "Home shows" in text
    assert "Element not clickable within 30s" in text
    assert "Started 27 Oct 2026, 18:43" in text


def test_names_are_escaped(tmp_path):
    text = run_report.build(make(tmp_path), tmp_path, "2026-10-27_18-43-01").read_text(encoding="utf-8")
    assert "<b>" not in text.split("<h4>")[1].split("</h4>")[0]
    assert "&lt;b&gt;" in text


def test_failed_tests_come_first_in_their_folder(tmp_path):
    text = run_report.build(make(tmp_path), tmp_path, "2026-10-27_18-43-01").read_text(encoding="utf-8")
    assert text.index("Basic: bad") < text.index("Basic: ok")


def test_no_results_writes_nothing(tmp_path):
    assert run_report.build([], tmp_path, "2026-10-27_18-43-01") is None
    assert not (tmp_path / "Reports").exists()


def test_error_line_prefers_the_named_exception(tmp_path):
    text = "tests/x.py:1: in test\nE   AssertionError: Receipt should show\nE   assert False\nE    +  where False = f()"
    assert run_report.error_line(text) == "AssertionError: Receipt should show"
    chain = "E   selenium.common.exceptions.TimeoutException: Message:\nE   framework.exceptions.FrameworkException: Element not clickable within 30s"
    assert run_report.error_line(chain) == "framework.exceptions.FrameworkException: Element not clickable within 30s"
    assert run_report.error_line("E   plain text only") == "plain text only"
    assert run_report.error_line("") == ""
