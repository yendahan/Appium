# Appium Java Automation (Bayad staging, Android)

Java 17, Maven, TestNG, Appium Java Client 11, Page Object Model. See README.md for setup.

## Commands
- `mvn test` runs only the device-free `unit` group (default).
- `mvn test -Dgroups=device -Denv=qa -Ddevice=emulator` runs the device tests; needs Appium on :4723 and an emulator.
- Add `-Dtest=SendMoneyTest` for one class. Without `-Dgroups=device` it finds nothing.
- Credentials come only from env vars `TEST_USERNAME` and `TEST_PASSWORD`. Never write them to a file.

## Layout (src/test/java)
- `pages/` page objects (locators live here only), `tests/device/` device tests, `tests/unit/` unit tests.
- `actions/MobileActions` is the only place that touches the driver (waits, tap, type, swipe, screenshot).
- `listeners/TestListener` saves screenshots to `target/artifacts/screenshots/<run date-time>/PASSED|FAILED|RECEIPT`.
- Test data is in `src/test/resources/testdata/<env>.json`, loaded with `TestDataLoader`.

## Rules
- New page objects extend `BasePage` and delegate every interaction to `actions`.
- Never use `Thread.sleep`; use `MobileActions` waits.
- This project has a sibling copy one directory up (`../`). Keep the two in sync, or delete one.

## Gotchas
- Send Money tests tap CONFIRM and move real Php 10 on staging per test (six per run). Do not run them casually.
- `LoginTest` sends wrong passwords and can lock the test accounts ("blocked temporarily").
- The Appium server runs without `adb_shell`, so avoid `mobile: shell`.
- Intermittent emulator network loss or app crashes cause one-off failures; rerun before changing code.
