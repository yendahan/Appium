# Appium Python Automation (Android / UiAutomator2)

Python 3.9+ · pytest · Appium-Python-Client · Selenium 4 · Page Object Model

Ported from the Java/TestNG framework, which is preserved on the `java-main` branch.

## Layout

| Path | Purpose |
|---|---|
| `framework/config_manager.py` | Layered config: `--cfg` > env var > device profile > env profile > defaults |
| `framework/driver_factory.py` | Builds the Android driver (UiAutomator2) from config |
| `framework/mobile_actions.py`, `gesture_validator.py` | Explicit waits, tap, type, swipe, scroll-to-text, screenshots; validated arguments |
| `framework/locator_parser.py` | `strategy=value` strings (`id`, `accessibilityId`, `xpath`, `className`, `text`) |
| `framework/test_data_loader.py` | JSON test data; `${env:NAME}` resolved from environment variables (no secrets in repo) |
| `framework/zephyr_client.py`, `zephyr_reporter.py` | Optional Zephyr Scale reporting for tests marked `@pytest.mark.zephyr("KEY")` |
| `pages/` | Page objects (locators live here only) |
| `conftest.py` | `--env/--device/--cfg` options, per-test `driver` fixture, screenshots/page source/logcat, Zephyr publishing |
| `tests/unit/` | Device-free tests (marker `unit`, the default) |
| `tests/device/` | Tests needing Appium + a device (marker `device`; money/lockout tests also `risky`) |
| `config/`, `testdata/` | `default.properties`, `env/<env>.properties`, `devices/<device>.properties`; `<env>.json` and QR images |

## Setup (macOS)

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
brew install node && npm install -g appium && appium driver install uiautomator2
export ANDROID_HOME="$HOME/Library/Android/sdk"
export PATH="$PATH:$ANDROID_HOME/platform-tools:$ANDROID_HOME/emulator"
adb version && appium driver list --installed
```

Start an emulator (`emulator -avd <name>`) or connect a device and confirm with `adb devices`.

## Configure

1. App under test: `config/env/qa.properties` sets `app.package`/`app.activity` (or `app.path` for an APK) and `app.landing.locator`.
2. Device: `--device emulator|physical`. For several devices set `device.udid` (env var `DEVICE_UDID`).
3. Secrets never go in files: `export TEST_USERNAME=<10-digit mobile, no leading 0> TEST_PASSWORD=<password>`.
4. Any key can be overridden: `--cfg appium.url=http://host:4723` or env var `APPIUM_URL`.

## Run

```bash
pytest                                              # unit tests only (default)
appium                                              # in another terminal
pytest -m "device and not risky" --env qa --device emulator   # safe device tests (app launch)
pytest -m device --env qa --device emulator         # ALL device tests, including risky ones
pytest -m device --device physical --cfg device.udid=<serial>
```

Artifacts: `artifacts/screenshots/<run>/PASSED|FAILED|RECEIPT`, `artifacts/diagnostics/` (page source, logcat on failure).
Careful: `test_send_money.py` moves real Php 10 on staging per test and `test_login.py` can lock the test account.

## Adding tests

Create a page object extending `BasePage`, put locators in the page module, delegate every interaction to `self.actions`,
and write a pytest test using the `driver` fixture with `@pytest.mark.device`. Never use `time.sleep`; use `MobileActions` waits.

## Zephyr Scale reporting (optional)

Mark tests with `@pytest.mark.zephyr("AMW-T1130")`. Set `ZEPHYR_TOKEN` (never in a file) and optionally
`ZEPHYR_PROJECT_KEY`, `ZEPHYR_CYCLE_KEY` (reuse a cycle; unset creates one per run), `ZEPHYR_CASES_FOLDER`
(default `Mobile Automation`) and `ZEPHYR_ARTIFACTS_LINK` (shared screenshot folder URL, shown in the last step's
actual result). Without a token the reporter does nothing and Jira errors never change a test result.
At the start of a run every case in the folder is listed as *Not Executed*; each test that runs updates its row to
Pass / Fail / Blocked. The case keys in the markers are fixed in code and must match the Zephyr project.
