You are working in the Bayad web repo: Playwright web UI automation for the Bayad staging web app
(Python 3.9+, pytest, pytest-playwright / playwright, Page Object Model). Patterned on the
Appium-Python project (Android; same product, same accounts and flows). Read CLAUDE.md and README.md first.

## Architecture
- `framework/web_actions.py` WebActions is the only code that touches `page`: auto-waiting
  click/fill/expect_visible, is_visible, text, select, upload, screenshot, page_source (`page.content()`).
  Prefer get_by_role / get_by_label / get_by_test_id over CSS/XPath.
- `pages/` hold locators only. Each extends BasePage, delegates every interaction to `self.actions`,
  and returns the next page object or `self`.
- `conftest.py`: options --env / --browser (chromium|firefox|webkit) / --viewport / --cfg / --headed,
  a function-scoped isolated BrowserContext + `page` fixture, and a makereport hook saving screenshots
  (PASSED/FAILED/RECEIPT), trace.zip, video and HAR on failure.
- Config precedence: --cfg > env var (KEY upper-cased, "." -> "_") > browsers/<name>.properties >
  env/<env>.properties > default.properties. Read it through ConfigManager, never os.environ directly.
- Test data: `testdata/<env>.json` via TestDataLoader (`${env:NAME}` placeholders resolved from env vars).
- Logged-in state: log in once per account and store `storage_state` (`.auth/<account>.json`, gitignored).
  Tests marked `@pytest.mark.shared_session("<credentials node>")` reuse it; payment, login and
  registration tests always get a fresh context. This replaces `--reuse-app`.

## Commands
- Default (safe): `pytest` -> unit tests only (`-m unit` in pytest.ini)
- Browser tests: `pytest -m e2e --env qa --browser chromium` (needs `playwright install chromium`)
- Safe only: `pytest -m "e2e and not risky"`; single test: `-k name` or a file path (quote paths with spaces)
- Debug: `--headed --slowmo 300`, `PWDEBUG=1`, `playwright show-trace <trace.zip>`

## Safety (non-negotiable)
- Never run `-m e2e` alone or `-m risky` without asking me first: it includes real payments and
  wrong-password logins that can lock accounts on staging. Money flows tap the final CONFIRM.
- Credentials only from TEST_USERNAME / TEST_PASSWORD (Asenso: ASENSO_*, Basic: BASIC_*, registration:
  REG_MOBILE / REG_PASSWORD). Never write them, ZEPHYR_TOKEN, storage_state files or traces to git.
  Traces, HAR and storage_state can contain tokens: keep them out of shared folders.
- No `time.sleep` / `page.wait_for_timeout`; use auto-waiting and `expect(...)` assertions
  (explicit timeouts for slow pages, ~60s for billers and receipts).
- No `force=True` clicks, no `networkidle` waits, no positional locators (`nth`) unless the DOM gives no better handle.
- A one-off failure from network loss or staging slowness: rerun before changing code.
- Zephyr is optional; with ZEPHYR_TOKEN set, ZEPHYR_CYCLE_NAME and ZEPHYR_CASES_FOLDER are required.

## Recipes
- New page: subclass BasePage, locators as class constants, delegate to actions, return the next page.
- New test: `tests/<Area>/<Account type>/test_*.py`; `pytestmark = [pytest.mark.e2e]` (+ `risky` if it
  moves money or sends bad logins); module-scoped TestDataLoader fixture; reuse the shared login helper.
- Mobile -> web mapping: tap_at / percent taps -> role or label locators; swipe / scroll_to_text ->
  `locator.scroll_into_view_if_needed()`; custom OTP boxes -> `keyboard.type` / `press_sequentially`;
  avatar upload -> `set_input_files`; page_source -> `page.content()`.
- New config key: add it to default.properties, override per env/browser only when it differs.
- Framework logic (parsers, config, loader, zephyr) gets a browser-free test in `tests/unit/` (marker `unit`).

## Known quirks
- Billers and receipt pages load slowly (up to ~60s). The staging OTP is `111111` unless `REG_OTP` is set.
- A mobile number can register only once: use a new `REG_MOBILE` every run.
- Don't copy organisation-private OneDrive paths into docs.

## How to work
1. Inspect the relevant files before editing, and match the surrounding style.
2. Run `pytest` (unit tests) after every change. Run browser tests only with my approval.
3. Keep changes minimal. Commit only when I ask.
4. Report what you ran and what passed or failed, plainly.

## Task
<describe the task here>
