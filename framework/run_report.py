"""One self-contained HTML report per pytest run: totals, per-folder counts, and one row per test with its scenario and result screenshot.

Written at the end of a run (see ``conftest.pytest_sessionfinish``) to ``<artifacts.dir>/Reports/<run folder>.html``.
Only test ids, outcomes, error lines and screenshots go in; the environment (credentials) is never read.
"""
from __future__ import annotations

import base64
import html
import io
import re
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Sequence

LOG = logging.getLogger(__name__)

THUMB_WIDTH = 420
MAX_ERROR_CHARS = 300

try:  # Pillow shrinks the screenshots so a run of ~70 tests stays a few MB
    from PIL import Image
except ImportError:  # pragma: no cover - without Pillow the report links the PNG instead
    Image = None


@dataclass
class TestResult:
    __test__ = False  # not a pytest test class despite the name

    nodeid: str
    folder: str  # the folder of the test file under tests/Android, e.g. "Basic Account"
    name: str
    outcome: str  # passed | failed | skipped
    doc: str = ""
    error: str = ""
    error_text: str = ""  # every error line of the failure, to find the failing step
    screenshot: Optional[Path] = None
    steps: Optional[Sequence[tuple]] = None  # (action, expected) pairs from the Zephyr case
    objective: str = ""


def error_text(longrepr_text: str) -> str:
    """All 'E   ' lines of a pytest failure, joined."""
    return " ".join(ln[1:].strip() for ln in (longrepr_text or "").splitlines() if ln.startswith("E "))[:2000]


def error_line(longrepr_text: str) -> str:
    """The failure message of a pytest failure: the last 'E   ' line that names an exception (``AssertionError: ...``), else the last line, trimmed."""
    lines = [ln[1:].strip() for ln in (longrepr_text or "").splitlines() if ln.startswith("E ")]
    named = [ln for ln in lines if re.match(r"^[\w.]*(Error|Exception)\b", ln)]
    text = named[-1] if named else (lines[-1] if lines else "")
    return text[:MAX_ERROR_CHARS]


def _thumb(path: Optional[Path]) -> str:
    if not path or not Path(path).is_file():
        return ""
    if Image is None:
        return f'<div class="noshot">{html.escape(str(path))}</div>'
    try:
        with Image.open(path) as img:
            img = img.convert("RGB")
            img.thumbnail((THUMB_WIDTH, THUMB_WIDTH * 3))
            buf = io.BytesIO()
            img.save(buf, "JPEG", quality=60)
        data = base64.b64encode(buf.getvalue()).decode()
        return f'<img class="shot" loading="lazy" alt="Result screenshot" src="data:image/jpeg;base64,{data}">'
    except OSError as e:
        LOG.warning("Report: could not read screenshot %s: %s", path, e)
        return ""


def _steps(result: TestResult) -> str:
    esc = html.escape
    if result.steps:
        items = "".join(f'<li><span class="act">{esc(a)}</span><span class="exp">{esc(e)}</span></li>' for a, e in result.steps)
        return f'<p class="obj">{esc(result.objective)}</p><ol class="steps">{items}</ol>'
    return f'<p class="obj">{esc(result.doc)}</p>' if result.doc else ""


def _row(result: TestResult) -> str:
    esc = html.escape
    status = {"passed": "Passed", "failed": "Failed"}.get(result.outcome, "Skipped")
    css = "pass" if result.outcome == "passed" else "fail" if result.outcome == "failed" else "skip"
    why = f'<div class="why">{esc(result.error)}</div>' if result.outcome == "failed" and result.error else ""
    scenario = _steps(result)
    details = f"<details><summary>Scenario and steps</summary>{scenario}</details>" if scenario else ""
    return (f'<article class="test {css}">{_thumb(result.screenshot)}<div class="info"><div class="head">'
            f'<span class="pill {css}">{status}</span><h4>{esc(result.name)}</h4></div>'
            f'<div class="file">{esc(result.nodeid)}</div>{why}{details}</div></article>')


CSS = """
:root{--bg:#f5f6f4;--surface:#fff;--ink:#17201d;--muted:#5d6a65;--line:#dde2de;--pass:#1f7a54;--pass-bg:#e1f1e8;--fail:#b8322a;--fail-bg:#f9e4e1;--accent:#1d4e6b;
--sans:system-ui,-apple-system,"Segoe UI",sans-serif;--mono:ui-monospace,Menlo,monospace}
@media (prefers-color-scheme: dark){:root{--bg:#0f1513;--surface:#18201d;--ink:#e6ece8;--muted:#98a6a0;--line:#2a3531;--pass:#58c496;--pass-bg:#16332a;--fail:#f0877e;--fail-bg:#3a1f1c;--accent:#7fb7d6;color-scheme:dark}}
body{background:var(--bg);color:var(--ink);font:15px/1.5 var(--sans);margin:0;padding:28px max(16px,env(safe-area-inset-right,0px)) 56px max(16px,env(safe-area-inset-left,0px))}
.wrap{max-width:980px;margin:0 auto;display:flex;flex-direction:column;gap:26px}h1{font-size:26px;margin:0}h3{margin:0;font-size:18px}h4{margin:0;font-size:15px}
.meta{color:var(--muted);font:13px var(--mono)}.totals{display:flex;flex-wrap:wrap;gap:10px 28px;margin-top:14px}.big{font-size:40px;font-weight:600;line-height:1}.big small{display:block;font-size:13px;font-weight:400;color:var(--muted)}
.ok{color:var(--pass)}.bad{color:var(--fail)}.fh{display:flex;flex-wrap:wrap;justify-content:space-between;gap:4px 16px;align-items:baseline}.fc{color:var(--muted);font-size:14px}
.bar{height:6px;background:var(--fail-bg);border-radius:3px;margin:8px 0 12px;overflow:hidden}.bar i{display:block;height:100%;background:var(--pass)}
.tests{display:flex;flex-direction:column;gap:10px}.test{display:grid;grid-template-columns:140px minmax(0,1fr);gap:14px;background:var(--surface);border:1px solid var(--line);border-radius:6px;padding:12px;border-left-width:4px}
.test.pass{border-left-color:var(--pass)}.test.fail{border-left-color:var(--fail)}.test.skip{border-left-color:var(--muted)}
.shot{width:140px;border-radius:4px;border:1px solid var(--line);cursor:zoom-in;align-self:start}.shot.big{position:fixed;inset:0;margin:auto;width:auto;max-height:92vh;max-width:92vw;z-index:20;cursor:zoom-out;box-shadow:0 0 0 100vmax rgba(0,0,0,.7)}
.noshot{font:12px var(--mono);color:var(--muted);overflow-wrap:anywhere}.info{min-width:0;display:flex;flex-direction:column;gap:6px}.head{display:flex;flex-wrap:wrap;align-items:center;gap:8px}
.pill{font-size:12px;font-weight:600;padding:2px 9px;border-radius:10px}.pill.pass{background:var(--pass-bg);color:var(--pass)}.pill.fail{background:var(--fail-bg);color:var(--fail)}.pill.skip{background:var(--line);color:var(--muted)}
.file{font:12px var(--mono);color:var(--muted);overflow-wrap:anywhere}.why{background:var(--fail-bg);border-radius:4px;padding:8px 10px;font:13px var(--mono);overflow-wrap:anywhere}
summary{cursor:pointer;color:var(--accent);font-size:14px}.obj{margin:8px 0;color:var(--muted);font-size:14px}.steps{margin:0;padding-left:20px;display:flex;flex-direction:column;gap:6px;font-size:14px}
.steps .exp{display:block;color:var(--muted)}.steps .exp::before{content:"Expect: ";font-weight:500}@media (max-width:560px){.test{grid-template-columns:1fr}}
"""
SCRIPT = ('document.addEventListener("click",function(e){var t=e.target;if(t.classList&&t.classList.contains("shot")){t.classList.toggle("big")}});'
          'document.addEventListener("keydown",function(e){if(e.key==="Escape"){document.querySelectorAll(".shot.big").forEach(function(i){i.classList.remove("big")})}});')


def render(results: Sequence[TestResult], run_folder: str) -> str:
    esc = html.escape
    passed = sum(r.outcome == "passed" for r in results)
    failed = sum(r.outcome == "failed" for r in results)
    total = len(results)
    rate = round(100 * passed / total) if total else 0
    folders: Dict[str, List[TestResult]] = {}
    for r in results:
        folders.setdefault(r.folder or "Tests", []).append(r)
    sections = []
    for folder, rows in folders.items():
        p = sum(r.outcome == "passed" for r in rows)
        f = sum(r.outcome == "failed" for r in rows)
        pct = round(100 * p / len(rows))
        ordered = sorted(rows, key=lambda r: (r.outcome != "failed", r.nodeid))
        sections.append(
            f'<section><div class="fh"><h3>{esc(folder)}</h3><span class="fc"><b>{p}</b> passed · <b class="bad">{f}</b> failed · {len(rows)} tests</span></div>'
            f'<div class="bar"><i style="width:{pct}%"></i></div><div class="tests">{"".join(_row(r) for r in ordered)}</div></section>')
    started = datetime.strptime(run_folder, "%Y-%m-%d_%H-%M-%S").strftime("%d %b %Y, %H:%M") if _is_run_folder(run_folder) else run_folder
    return (f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>Run report {esc(run_folder)}</title><style>{CSS}</style></head><body><div class="wrap"><header><h1>Test run report</h1>'
            f'<div class="meta">Started {esc(started)}</div><div class="totals"><div class="big ok">{passed}<small>passed</small></div>'
            f'<div class="big bad">{failed}<small>failed</small></div><div class="big">{rate}%<small>of {total} tests</small></div></div></header>'
            f'{"".join(sections)}<div class="meta">One result screenshot per test; tap an image to enlarge.</div></div><script>{SCRIPT}</script></body></html>')


def _is_run_folder(text: str) -> bool:
    try:
        datetime.strptime(text, "%Y-%m-%d_%H-%M-%S")
        return True
    except ValueError:
        return False


def build(results: Sequence[TestResult], artifacts_dir: Path, run_folder: str) -> Optional[Path]:
    """Writes <artifacts_dir>/Reports/<run_folder>.html and returns its path; None when no test ran."""
    if not results:
        return None
    target = Path(artifacts_dir) / "Reports" / f"{run_folder}.html"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(render(results, run_folder), encoding="utf-8")
    return target
