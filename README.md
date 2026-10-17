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
| `base/BaseTest` | New session per test, always quit; attaches `TestListener` and `ZephyrReporter` |
| `listeners/TestListener` | Screenshot on pass and fail; on failure also page source and logcat → `target/artifacts`, linked from the HTML report |
| `listeners/ZephyrReporter`, `ZephyrCase`, `integrations/ZephyrClient` | Optional: publishes results of `@ZephyrCase`-annotated tests to a Zephyr Scale test cycle (see [Jira / Zephyr Scale](#jira--zephyr-scale-reporting-optional)) |
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

## Jira / Zephyr Scale reporting (optional)

Results of tests annotated with `@ZephyrCase("<test case key>")` are published to a Zephyr Scale (Cloud, API v2) test
cycle. View them in Jira under your project's **Zephyr Scale > Test Cycles**. Currently wired to project `AMW`
(cases `AMW-T1130` to `AMW-T1141`, folder `Mobile Automation`).

### Setup

1. **Test cases**: create them in Zephyr (name, plus steps with expected results on the Test Script tab), then annotate
   the matching test method: `@ZephyrCase("AMW-T1130")` (import `listeners.ZephyrCase`).
2. **Project key**: `AMW` is only the default in `default.properties`. Override it on any run (highest priority first):
   `-Dzephyr.project.key=<KEY>`, then env var `ZEPHYR_PROJECT_KEY`, then `env/<env>.properties`. For example
   `export ZEPHYR_PROJECT_KEY=OTHER`. Optional `zephyr.base.url` (default `https://api.zephyrscale.smartbear.com/v2`).
3. **Token**: create it in Zephyr Scale > profile > Access Tokens and export it. Never put it in a file:
   `export ZEPHYR_TOKEN=<token>`.
4. **Cycle** (optional): create a cycle in Zephyr Scale > Test Cycles and set its key (looks like `AMW-R204`, with the `R`):
   `export ZEPHYR_CYCLE_KEY=AMW-R204` (or `zephyr.cycle.key`). Every run then reuses it. If unset, each run creates a
   new cycle named `Automation <env>/<device> <date time>`. The key is not validated: a wrong or deleted key makes the
   run pass but publish nothing (look for `Zephyr: cycle <key> lists N cases` in the log).
5. **Screenshot folder** (optional): save screenshots into a synced OneDrive folder and give Zephyr a link to it:
   `export ARTIFACTS_DIR="$HOME/Library/CloudStorage/OneDrive-<org>/CIS/Automation Screenshots/Bayad App"` and
   `export ZEPHYR_ARTIFACTS_LINK="<shared folder URL>"` (or `-Dzephyr.artifacts.link`). The URL is organisation-private:
   set it per run, never commit it.

Without `ZEPHYR_TOKEN` and a project key the reporter does nothing. Jira errors are only logged and never change a
test result.

### What gets published

- **All cases in every run**: at the start of a run every case in the Zephyr folder `Mobile Automation` (override with
  `zephyr.cases.folder`) is put in the cycle as *Not Executed* (or reset to it when the cycle is reused). Each test that
  runs updates its own row to Pass / Fail / Blocked, so tests you skip (e.g. Send Money) stay Not Executed.
- **Expected results**: the case's steps are copied into the execution. The reporter sets every step to the test's
  overall status with the actual result (`As expected`, or the exception message). It cannot tell which step failed.
- **Screenshots**: not uploaded as attachments (the Zephyr Cloud API has no documented attachment upload for
  executions) and the image cannot be shown inside the field (tested). The **Actual Result of the last step** shows
  `Screenshot: OneDrive folder > <run>/<PASSED|FAILED>/<file>.png`: the first part links to the shared folder
  (`ZEPHYR_ARTIFACTS_LINK`), the second is the short path to find the file inside it. Without the link only the short
  path is shown. The link only opens for people in your organization who have access to the folder. The execution
  comment holds only the failure text, if any, and failure text in the Actual Result is HTML-escaped.

### Example full run

```bash
export TEST_USERNAME=<10-digit mobile> TEST_PASSWORD=<password>
export ZEPHYR_TOKEN=<token> ZEPHYR_PROJECT_KEY=AMW ZEPHYR_CYCLE_KEY=AMW-R204
export ZEPHYR_CASES_FOLDER="Mobile Automation"   # optional, this is the default
export ARTIFACTS_DIR="$HOME/Library/CloudStorage/OneDrive-<org>/CIS/Automation Screenshots/Bayad App"
export ZEPHYR_ARTIFACTS_LINK="<shared folder URL>"   # optional
mvn test -Dgroups=device -Denv=qa -Ddevice=emulator
```

Careful: `SendMoneyTest` moves real Php 10 on staging per test and `LoginTest` can lock the test account. For a safe check
run one class, e.g. `-Dtest=AppLaunchTest`.

### Using a different Zephyr project

1. Set the project key for the run: `export ZEPHYR_PROJECT_KEY=<KEY>` (or `-Dzephyr.project.key=<KEY>`).
2. Use a token that has access to that project, and a cycle key from it (`ZEPHYR_CYCLE_KEY`), or unset the cycle key to
   create a new cycle for the run.
3. Create the test cases there, in a folder named `Mobile Automation`, or set the folder name for the run:
   `export ZEPHYR_CASES_FOLDER="My Folder"` (or `-Dzephyr.cases.folder="My Folder"`). It must match the Zephyr folder
   exactly. The folder and cases must already exist: the run does not create them. If the name is wrong the run still
   passes but the cycle lists no cases (log: `Zephyr: cycle <key> lists 0 cases`). This also applies to the first run.
4. Update the `@ZephyrCase("AMW-T...")` keys in `tests/device/*`. They are fixed in the code and do not follow the
   project key setting, so they must match the new project's case keys.
