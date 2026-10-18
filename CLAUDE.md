# Appium Python Automation (Bayad staging, Android)

Python 3.9+, pytest, Appium-Python-Client, Page Object Model. Ported from the Java/TestNG project (kept on branch `java-main`). See README.md for setup.

## Commands
- `pytest` runs only the device-free `unit` tests (default, `-m unit` in pytest.ini).
- `pytest -m device --env qa --device emulator` runs device tests; needs Appium on :4723 and an emulator.
- `pytest -m "device and not risky"` runs only the safe device tests (app launch).
- Add `-k test_name` or a file path for a single test. `--cfg key=value` overrides any config key.
- Credentials come only from env vars `TEST_USERNAME` and `TEST_PASSWORD`. Never write them to a file.

## Layout
- `pages/` page objects (locators live here only), `tests/device/` device tests, `tests/unit/` unit tests.
- `framework/mobile_actions.py` is the only place that touches the driver (waits, tap, type, swipe, screenshot).
- `conftest.py` saves screenshots to `artifacts/screenshots/<run date-time>/PASSED|FAILED|RECEIPT` and publishes Zephyr results.
- Test data is in `testdata/<env>.json`, loaded with `TestDataLoader`; config in `config/` (default < env < device < env var < `--cfg`).

## Rules
- New page objects extend `BasePage` and delegate every interaction to `actions`.
- Never use `time.sleep` for waiting; use `MobileActions` waits.
- Mark device tests `@pytest.mark.device`; tests that move money or send bad logins also `@pytest.mark.risky`.

## Gotchas
- Send Money tests tap CONFIRM and move real Php 10 on staging per test (six per run). Do not run them casually.
- `test_login.py` sends wrong passwords and can lock the test accounts ("blocked temporarily").
- The Appium server runs without `adb_shell`, so avoid `mobile: shell`.
- Intermittent emulator network loss or app crashes cause one-off failures; rerun before changing code.
