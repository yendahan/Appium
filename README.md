# Appium Java Automation (Android / UiAutomator2)

Java 17 · Maven · TestNG · Appium Java Client 11.0.0 · Selenium 4.51.0 · Page Object Model

`java-client` 11.0.0 requires `selenium-api >= 4.50`, hence the pinned Selenium 4.51.0 (see `pom.xml`).

## Layout

| Path (under `src/test/java` unless noted) | Purpose |
|---|---|
| `config/ConfigManager` | Layered config: `-D` > env var > device profile > env profile > defaults |
| `driver/AppiumDriverFactory`, `DriverManager` | Builds `AndroidDriver` (UiAutomator2) from config; per-thread holder |
| `actions/MobileActions`, `GestureValidator` | Explicit waits, tap, type, swipe, scroll-to-text, screenshots; validated arguments |
| `pages/BasePage`, `LandingPage` | Page objects (locator for the landing screen comes from config) |
| `base/BaseTest` | New session per test, always quit; attaches `TestListener` |
| `listeners/TestListener` | On failure: screenshot, page source, logcat → `target/artifacts`, linked from the HTML report |
| `data/TestDataLoader` | JSON test data; `${env:NAME}` resolved from environment variables (no secrets in repo) |
| `tests/unit/*` | Device-free tests (config, locators, data, gesture validation) — group `unit` |
| `tests/device/*` | Tests that need Appium + a device — group `device` |
| `src/test/resources/config/**` | `default.properties`, `env/<env>.properties`, `devices/<device>.properties` |
| `src/test/resources/testdata/<env>.json` | External test data |

## macOS setup

```bash
# Java 17 (the build uses `--release 17`; any JDK >= 17 works)
brew install --cask temurin@17
# Node + Appium + driver
brew install node
npm install -g appium
appium driver install uiautomator2
# Android SDK: install Android Studio (or cmdline-tools), then add to ~/.zshrc:
export ANDROID_HOME="$HOME/Library/Android/sdk"
export PATH="$PATH:$ANDROID_HOME/platform-tools:$ANDROID_HOME/emulator"
adb version && appium driver list --installed
```

Emulator: create an AVD in Android Studio, start it (`emulator -avd <name>`), confirm with `adb devices`.
Physical device: enable Developer options + USB debugging, connect, accept the RSA prompt, confirm with `adb devices`.

## Configure

1. App under test — in `config/env/qa.properties` (or `-D` / env vars), set **either** `app.path` (APK) **or**
   both `app.package` and `app.activity`; and `app.landing.locator` (`id=...`, `accessibilityId=...`,
   `xpath=...`, `className=...`, `text=...`) for an element visible after launch.
2. Device — pick a profile with `-Ddevice=emulator|physical`. For several attached devices set `device.udid`
   (env var `DEVICE_UDID`). Optional `device.avd`, `device.platformVersion`.
3. Secrets — never commit them. Export them, e.g. `export TEST_USERNAME=... TEST_PASSWORD=...`; test data
   references them as `${env:TEST_USERNAME}`.
4. Login tests need valid credentials in the environment (never in files):
   `export TEST_USERNAME=<10-digit mobile, no leading 0> TEST_PASSWORD=<password>`.
   The app's mobile field accepts only 10 characters, so a leading 0 makes the number wrong.
5. Any key can be overridden: `-Dappium.url=http://host:4723` or env var `APPIUM_URL`.

## Run

```bash
mvn test                                    # device-free unit tests (default group)
appium                                      # in another terminal (default http://127.0.0.1:4723)
mvn test -Dgroups=device -Denv=qa -Ddevice=emulator   # needs TEST_USERNAME / TEST_PASSWORD
mvn test -Dgroups=device -Ddevice=physical -Ddevice.udid=<serial>
```

Reports: `target/surefire-reports/index.html` (TestNG HTML; failure screenshots are embedded/linked),
`target/artifacts/` (screenshots, page source, logcat), `target/logs/test-run.log`.

## Adding tests

Create a page object extending `BasePage`, put locators in the page class, delegate every interaction to
`actions`, and extend `BaseTest` with `@Test(groups = "device")`. Never use `Thread.sleep`; use `MobileActions` waits.
