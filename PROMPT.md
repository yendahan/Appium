You are working in the Appium-Python repo: Android UI automation for the Bayad staging app
(Python 3.9+, pytest, Appium-Python-Client 4/5, Selenium 4, UiAutomator2, Page Object Model).
It was ported from Java/TestNG, which lives on branch `java-main`. Read CLAUDE.md and README.md first.

## Architecture
- `framework/mobile_actions.py` MobileActions is the only code that touches the driver
  (wait_visible/clickable, is_visible, tap, type, clear, text, swipe, scroll_to_text, screenshot, page_source).
  Locators are (by, value) tuples, parsed by `locator_parser.parse("strategy=value")`.
- `pages/` hold locators only. Each extends BasePage, delegates to `self.actions`, and returns the next
  page object or `self`. Flow: PrivacyNotice -> Welcome -> Login -> BiometricSetup -> Home -> SendMoney.
- `conftest.py` provides options --env/--device/--cfg, a function-scoped `driver` fixture, and a makereport
  hook that saves screenshots (PASSED/FAILED), page source and logcat on failure, and publishes Zephyr results
  for tests carrying `@pytest.mark.zephyr("AMW-Txxxx")`.
- Config precedence: --cfg > env var (KEY upper-cased, "." -> "_") > devices/<device>.properties >
  env/<env>.properties > default.properties. Read it through ConfigManager, never os.environ directly.
- Test data: `testdata/<env>.json` via TestDataLoader (`${env:NAME}` placeholders). `dev.json` has no
  `sendMoney` section, so send-money tests only run with `--env qa`.

## Safety (non-negotiable)
- Plain `pytest` runs unit tests only. Never run `-m device` or `-m risky` without asking me first.
  Safe device run: `pytest -m "device and not risky"`. Note that `-m device` alone includes risky tests.
- Send-money tests move real Php 10 each. test_login.py can lock accounts.
- Credentials come only from TEST_USERNAME / TEST_PASSWORD. Never write them, ZEPHYR_TOKEN, or any secret to a file.
- Avoid `mobile: shell` (the Appium server has no adb_shell). No `time.sleep`; use MobileActions waits.
- A one-off failure from emulator network loss or an app crash: rerun before changing code.

## Recipes
- New page: subclass BasePage, keep locators as class constants, delegate to actions, return the next page.
- New device test: put it in tests/device/, set `pytestmark = [device]` (+ `risky` if it moves money or
  sends bad logins), add `@pytest.mark.zephyr(...)` if a case exists, reuse `helpers.log_in_to_home`, load
  data with a module-scoped TestDataLoader fixture.
- New config key: add it to default.properties, override per env/device only when it differs.
- Framework logic (parsers, validators, config, loader) gets a device-free test in tests/unit/ (marker `unit`).

## Known quirks
- default.properties and the physical-device properties still carry Java-era comments (utils.LocatorParser, -Ddevice.udid).
- zephyr_reporter.py has a stray `import os`. Zephyr case keys are hard-coded, and cycle state is module-global.
- README/CLAUDE.md mention an organisation-private OneDrive path; don't copy it into new docs.

## How to work
1. Inspect the relevant files before editing, and match the surrounding style.
2. Run `pytest` (unit tests) after every change. Run device tests only with my approval.
3. Keep changes minimal. Commit only when I ask.
4. Report what you ran and what passed or failed, plainly.

## Task
<describe the task here>
