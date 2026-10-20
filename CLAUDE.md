# Appium Python Automation (Bayad staging, Android)

Python 3.9+, pytest, Appium-Python-Client, Page Object Model. Ported from the Java/TestNG project (kept on branch `java-main`). See README.md for setup.

## Commands
- `pytest` runs only the device-free `unit` tests (default, `-m unit` in pytest.ini).
- `pytest -m device --env qa --device emulator` runs device tests; needs Appium on :4723 and an emulator.
- `pytest -m "device and not risky"` runs only the safe device tests (app launch).
- Add `-k test_name` or a file path for a single test. `--cfg key=value` overrides any config key.
- Credentials come only from env vars `TEST_USERNAME` and `TEST_PASSWORD`. The Asenso tests use `ASENSO_USERNAME` and `ASENSO_PASSWORD` (testdata node `asensoCredentials`). Never write them to a file.
- Zephyr reporting is optional: with `ZEPHYR_TOKEN` set you must also set `ZEPHYR_CYCLE_NAME` and `ZEPHYR_CASES_FOLDER` (else the run stops). A run creates a new cycle, creates the folder if missing and the cases it lacks (`framework/zephyr_cases.py`); tests report to cases by name.

## Layout
- `pages/` page objects (locators live here only), `tests/Android/Upgraded Consumer Account/` device tests (`tests/Android/helpers.py` is shared), `tests/Android/Consumer Account with Asenso/` the same tests as `test_asenso_*.py` for an Asenso account (same risks and payments), `tests/Android/Asenso Account/` Asenso service tests (`test_asenso_account_*.py`, page object `pages/asenso_page.py`), `tests/unit/` unit tests.
- `framework/mobile_actions.py` is the only place that touches the driver (waits, tap, type, swipe, screenshot).
- `conftest.py` saves screenshots to `artifacts/Screenshots/<ZEPHYR_CASES_FOLDER>/<test folders under tests/>/<run date-time>/PASSED|FAILED|RECEIPT` and publishes Zephyr results.
- Test data is in `testdata/<env>.json`, loaded with `TestDataLoader`; config in `config/` (default < env < device < env var < `--cfg`).

## Rules
- New page objects extend `BasePage` and delegate every interaction to `actions`.
- Never use `time.sleep` for waiting; use `MobileActions` waits.
- Mark device tests `@pytest.mark.device`; tests that move money or send bad logins also `@pytest.mark.risky`.

## Gotchas
- `tests/Android/Asenso Account/`: add money, withdraw money (Php 300 each, between your own wallets) and pay bills (Php 30 + Php 10 fee) tap CONFIRM and are `risky`; my transactions and account management are safe. Over the Counter add money is "Coming soon", FAQ is untappable.
- Send Money tests tap CONFIRM and move real Php 10 on staging per test (six per run). Do not run them casually.
- `test_pay_via_qr.py` also taps CONFIRM (four payments per run): dynamic QRs pay Php 10, static QRs pay the amount encoded in the QR (e.g. Php 88.88).
- `test_send_money_via_bayad_wallet.py` repeats the six Send Money payments, entering from the Wallet tab (six more per run).
- `test_registration.py` registers a real staging account per run: set `REG_MOBILE` (a new number each run) and `REG_PASSWORD`, never stored; the test skips without them. OTP is `111111` unless `REG_OTP` is set.
- `test_pay_bills.py` pays Manila Water for real on staging: Php 30 plus a Php 10 fee per run. The billers and the receipt load slowly (up to ~60s), and the search button and result row are tapped by position.
- `test_login.py` sends wrong passwords and can lock the test accounts ("blocked temporarily").
- The Appium server runs without `adb_shell`, so avoid `mobile: shell`.
- Intermittent emulator network loss or app crashes cause one-off failures; rerun before changing code.
