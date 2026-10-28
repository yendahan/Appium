# Appium Python Automation (Bayad staging, Android)

Python 3.9+, pytest, Appium-Python-Client, Page Object Model. Ported from the Java/TestNG project (kept on branch `java-main`). See README.md for setup.

## Commands
- `pytest` runs only the device-free `unit` tests (default, `-m unit` in pytest.ini).
- `pytest -m device --env qa --device emulator` runs device tests; needs Appium on :4723 and an emulator.
- `pytest -m "device and not risky"` runs only the safe device tests (app launch).
- Add `--reuse-app` to let the tests marked `shared_session` (browse-only: wallet/Asenso/Basic transactions, account management, Basic add-money previews; plus the Send Money tests, which leave the receipt through DONE) share one logged-in app session per account; everything else keeps a fresh app per test. A failed test or an account switch closes the shared session.
- Add `-k test_name` or a file path for a single test. `--cfg key=value` overrides any config key.
- Credentials come only from env vars `TEST_USERNAME` and `TEST_PASSWORD`. The Asenso tests use `ASENSO_USERNAME` and `ASENSO_PASSWORD` (testdata node `asensoCredentials`). Never write them to a file.
- Zephyr reporting is optional: with `ZEPHYR_TOKEN` set you must also set `ZEPHYR_CYCLE_NAME` and `ZEPHYR_CASES_FOLDER` (else the run stops). A run creates a new cycle, creates the folder if missing and the cases it lacks (`framework/zephyr_cases.py`); tests report to cases by name.

## Layout
- `pages/` page objects (locators live here only), `tests/Android/Upgraded Consumer Account/` device tests (`tests/Android/helpers.py` is shared), `tests/Android/Consumer Account with Asenso/` the same tests as `test_asenso_*.py` for an Asenso account (same risks and payments), `tests/Android/Asenso Account/` Asenso service tests (`test_asenso_account_*.py`, page object `pages/asenso_page.py`), `tests/Android/Basic Account/` Basic account tests (`test_basic_account_*.py`, registration lives here; `BASIC_USERNAME`/`BASIC_PASSWORD`), `tests/unit/` unit tests.
- `framework/mobile_actions.py` is the only place that touches the driver (waits, tap, type, swipe, screenshot).
- Every device run writes an HTML report to `artifacts/Reports/<run date-time>.html` (totals, per-folder results, scenario steps and result screenshot per test; path printed at the end of the run).
- Every run also writes bug-report drafts for its failed tests to `artifacts/Reports/<run>/bugs/` (BUG-nn-*.md and bugs.json: steps, expected, actual, suggested cause such as network / locked account / test data, evidence paths). Nothing is created in Jira by the run: ask Claude to file them (give the Jira project key and issue type).
- `conftest.py` saves screenshots to `artifacts/Screenshots/<ZEPHYR_CASES_FOLDER>/<test folders under tests/>/<run date-time>/PASSED|FAILED|RECEIPT` and publishes Zephyr results.
- Test data is in `testdata/<env>.json`, loaded with `TestDataLoader`; config in `config/` (default < env < device < env var < `--cfg`).

## Rules
- New page objects extend `BasePage` and delegate every interaction to `actions`.
- Never use `time.sleep` for waiting; use `MobileActions` waits.
- Mark device tests `@pytest.mark.device`; tests that move money or send bad logins also `@pytest.mark.risky`.

## Gotchas
- `tests/Android/Asenso Account/`: add money, withdraw money (Php 300 each, between your own wallets) and pay bills (Php 30 + Php 10 fee) tap CONFIRM and are `risky`; my transactions and account management are safe. Over the Counter add money is "Coming soon", FAQ is untappable.
- `tests/Android/Accounts Registration/` runs only when its folder is named on the command line (conftest deselects it from `tests` and `tests/Android` runs). It registers and upgrades real staging accounts: `REG_MOBILE` (first number; registered ones are skipped by +1), `REG_PASSWORD`, `REG_COUNT` (how many, default 1).
- `tests/Android/OTP Sending Money/` is isolated the same way and completes six real sends (about Php 66,000): `OTP_MOBILE`, `OTP_PASSWORD`, optional `OTP_CODE`.
- Send Money tests tap CONFIRM and move real Php 10 on staging per test (six per run). Do not run them casually.
- The Pay via QR tests in `test_payments.py` also tap CONFIRM (four payments per run): dynamic QRs pay Php 10, static QRs pay the amount encoded in the QR (e.g. Php 88.88).
- `test_payments.py` (and `test_asenso_payments.py`) holds Send Money, Send Money from the Wallet tab (the six payments repeated) and Pay via QR; run all with one file path.
- `tests/Android/Basic Account/test_basic_account_registration.py` registers a real staging account per run: set `REG_MOBILE` (a new number each run) and `REG_PASSWORD`, never stored; the test skips without them. OTP is `111111` unless `REG_OTP` is set.
- `tests/Android/Basic Account/test_basic_account_upgrade.py` upgrades that same new account (same `REG_MOBILE`/`REG_PASSWORD`, run it right after registration): it submits the Upgrade Account wizard once per number (the app keeps its progress), taking the ID photos, selfie and video with the emulator camera.
- `test_pay_bills.py` pays Manila Water for real on staging: Php 30 plus a Php 10 fee per run. The billers and the receipt load slowly (up to ~60s), and the search button and result row are tapped by position.
- `test_login.py` sends wrong passwords and can lock the test accounts ("blocked temporarily").
- `tests/Android/Basic Account/test_basic_account_login.py` (biometric login) needs an emulator with a screen lock and an enrolled fingerprint (`adb shell locksettings set-pin 1234`, then Settings > Security > Fingerprint, touch with `adb emu finger touch 1`); it skips on a physical phone. It enables biometrics on the Basic account's fresh app session only, so other tests are unaffected.
- The Appium server runs without `adb_shell`, so avoid `mobile: shell`.
- Intermittent emulator network loss or app crashes cause one-off failures; rerun before changing code.
