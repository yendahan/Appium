# Appium Python Automation (Android / UiAutomator2)

Python 3.9+ · pytest · Appium-Python-Client · Selenium 4 · Page Object Model

Ported from the Java/TestNG framework, which is preserved on the `java-main` branch.

## Layout

| Path | Purpose |
|---|---|
| `framework/config_manager.py` | Layered config: `--cfg` > env var > device profile > env profile > defaults |
| `framework/driver_factory.py` | Builds the Android driver (UiAutomator2) from config |
| `framework/mobile_actions.py`, `gesture_validator.py` | Explicit waits, tap, type, swipe, scroll-to-text, screenshots; validated arguments. Also `tap_at` (screen position), `press_digits` (key presses for custom code boxes), `tap_present`, `hide_keyboard`, `scroll_to_description` |
| `framework/locator_parser.py` | `strategy=value` strings (`id`, `accessibilityId`, `xpath`, `className`, `text`) |
| `framework/test_data_loader.py` | JSON test data; `${env:NAME}` resolved from environment variables (no secrets in repo) |
| `framework/zephyr_client.py`, `zephyr_reporter.py` | Optional Zephyr Scale reporting for tests marked `@pytest.mark.zephyr("KEY")`: new cycle per run, case folder check, tests linked to cases by name |
| `framework/zephyr_cases.py` | The Zephyr case definition (name, objective, steps) of every device test (the Asenso copies are derived from them, names prefixed `Asenso `); used to fill an empty case folder |
| `scripts/create_zephyr_cases.py` | Creates those cases in a folder by hand (`--dry-run` first) |
| `pages/` | Page objects (locators live here only) |
| `conftest.py` | `--env/--device/--cfg` options, per-test `driver` fixture, screenshots/page source/logcat, Zephyr publishing, and the check that stops a run before any test when the Zephyr setup is wrong |
| `tests/unit/` | Device-free tests (marker `unit`, the default) |
| `tests/Android/Asenso Account/` | Device tests of the Asenso service (Services > See All > Asenso): add money, withdraw, pay bills, my transactions, Account Management links; logs in with `ASENSO_USERNAME` / `ASENSO_PASSWORD`; page object `pages/asenso_page.py` |
| `tests/Android/Consumer Account with Asenso/` | The same device tests as the folder below, as `test_asenso_*.py`, logging in with `ASENSO_USERNAME` / `ASENSO_PASSWORD`; same `risky` payments and lockouts |
| `tests/Android/Upgraded Consumer Account/` | Tests needing Appium + an Android device (marker `device`; money/lockout tests also `risky`); `tests/Android/helpers.py` holds the shared login helper |
| `config/`, `testdata/` | `default.properties`, `env/<env>.properties`, `devices/<device>.properties`; `<env>.json`, QR images and the registration avatar (`testdata/avatar/`) |

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

### First time with Zephyr Scale (optional)

Skip this if `ZEPHYR_TOKEN` is unset: the reporter is then off and tests run normally. To report to Zephyr, make sure these exist:

1. **Project `AMW`** in Jira with Zephyr Scale (`zephyr.project.key`; override with `ZEPHYR_PROJECT_KEY`).
2. **API token**: Jira profile > Zephyr Scale API Access Tokens, for a user allowed to create cycles and executions in AMW. Export it as `ZEPHYR_TOKEN`.
3. **Test cases**: nothing to create by hand. Every device test has a case definition (name, objective, steps) in `framework/zephyr_cases.py`, and the run creates the cases in its folder. A test reports only to the case **with its name** in the run's folder (its `@pytest.mark.zephyr` marker just says it reports to Zephyr; there are no fixed case keys).
4. **Test-case folder**: choose the top folder for the run with `ZEPHYR_CASES_FOLDER` (e.g. `export ZEPHYR_CASES_FOLDER="Regression"`; a `parent/child` path also works). Inside it the run mirrors the project's test folders: the cases go in `<your folder>/Android/Upgraded Consumer Account` `<your folder>/Android/Consumer Account with Asenso` (the same cases, names prefixed `Asenso `) and `<your folder>/Android/Asenso Account`, taken from where the test files sit under `tests/` (rename a project folder and Zephyr follows). **Any folder that does not exist is created**, so you can delete them and rerun. Each of those last folders gets every defined case it lacks (matched by name): an **existing case with the same name is moved in** (one in no folder first, otherwise one from another folder, lowest key first; it keeps its key and history, and the old folder loses it), and a new case is created only when no case with that name exists anywhere in the project. So deleting folders and rerunning does not pile up new cases. The cases live **only** in their last folder: a defined case found in an upper folder of the tree (`<your folder>` or `<your folder>/Android`, for example left by an older run) is moved down into it, and a duplicate there is taken out of the folder tree (not deleted), so it can be reused later. Other cases in those folders are not touched. At the start of a run every case in that folder is listed in the cycle as *Not Executed*, so cases you added or edited in Zephyr are picked up on the next run.
5. **Test cycle**: nothing to create. Every run makes a **new** cycle named `<ZEPHYR_CYCLE_NAME> <date time>` (e.g. `ZEPHYR_CYCLE_NAME="Regression"` gives `Regression 2026-10-19 17:30`). A cycle is never reused, so `ZEPHYR_CYCLE_KEY` is ignored (with a warning) if it is still exported.
6. **The run stops before any test starts** (exit code 2 and a message) when Zephyr is enabled (`ZEPHYR_TOKEN` is set and a selected test reports to Zephyr) and `ZEPHYR_CYCLE_NAME` or `ZEPHYR_CASES_FOLDER` is not set. Unit-only runs and runs without a token are not affected. The token's user must be allowed to create folders, cases and cycles in AMW. If creating the folder, its cases or the cycle fails, the run also stops before any test, with the reason (for example `could not create test case '...': 403 forbidden`); if the folder had just been created it stays, and running again fills it. To run without Zephyr, unset `ZEPHYR_TOKEN`.
7. **Screenshot folder (optional)**: a shared OneDrive/SharePoint folder; point `ARTIFACTS_DIR` at its local sync path and `ZEPHYR_ARTIFACTS_LINK` at its URL (organisation-private, do not commit).

## Configure

1. App under test: `config/env/qa.properties` sets `app.package`/`app.activity` (or `app.path` for an APK) and `app.landing.locator`.
2. Device: `--device emulator|physical`. For several devices set `device.udid` (env var `DEVICE_UDID`).
3. Secrets never go in files: `export TEST_USERNAME=<10-digit mobile, no leading 0> TEST_PASSWORD=<password>`.
   For the Asenso account tests also `export ASENSO_USERNAME=<10-digit mobile, no leading 0> ASENSO_PASSWORD=<password>` (without them the Asenso login tests fail).
   For the registration tests set `REG_MOBILE` (a new number each run) and `REG_PASSWORD` per run; `REG_OTP` is optional (default `111111`).
4. Any key can be overridden: `--cfg appium.url=http://host:4723` or env var `APPIUM_URL`.

## Run

```bash
pytest                                              # unit tests only (default)
appium                                              # in another terminal
pytest -m "device and not risky" --env qa --device emulator   # safe device tests (app launch)
pytest -m device --env qa --device emulator         # ALL device tests (both account folders), including risky ones
pytest -m "device and not risky" --env qa --device emulator "tests/Android/Consumer Account with Asenso"   # safe Asenso tests only
pytest -m device --device physical --cfg device.udid=<serial>
```

### Asenso consumer account tests

`tests/Android/Consumer Account with Asenso/` holds the same seven test files as `Upgraded Consumer Account`, named `test_asenso_*.py` (app launch, login, registration, pay bills, pay via QR, send money, send money via Bayad wallet). The app flow and page objects are the same; only the account differs. They log in with `ASENSO_USERNAME` / `ASENSO_PASSWORD` (testdata node `asensoCredentials`, never stored); every other test-data node (`sendMoney`, `payBills`, `registration`, QR images) is shared with the Upgraded tests. `sendMoney.bayadWalletNumber` holds the recipient numbers by account type (`upgraded`, `asenso`, `basic`): the Upgraded tests send to the Asenso account, the Asenso tests to the Upgraded one (`basic` is not used yet). Markers and risks are identical: the Send Money, Pay via QR and Pay Bills copies pay for real on staging, the login copy can lock the account, and the registration copy registers a real account. Their Zephyr cases are the Upgraded ones with an `Asenso ` prefix (e.g. `Asenso Login: wrong password is rejected`), in the `Android/Consumer Account with Asenso` folder. The Pay Bills and Registration sections below apply to the `test_asenso_pay_bills.py` and `test_asenso_registration.py` copies as well.

```bash
export ASENSO_USERNAME=<10-digit mobile, no leading 0> ASENSO_PASSWORD=<password>
pytest -m "device and not risky" --env qa --device emulator "tests/Android/Consumer Account with Asenso"   # safe: app launch only
pytest -m device --env qa --device emulator "tests/Android/Consumer Account with Asenso"                   # all of them, including risky
```

### Asenso Account tests

`tests/Android/Asenso Account/` (`test_asenso_account_*.py`) tests the Asenso service, opened with Services > See All > scroll down > Asenso, as the Asenso account (`ASENSO_USERNAME` / `ASENSO_PASSWORD`):

| Test | Marker | What it does |
|---|---|---|
| `add_money` | `risky` | Add Money > From My Bayad Wallet > Php 300 (`asensoAccount.addMoney.amount`) > NEXT > CONFIRM, expects a success message |
| `withdraw_money` | `risky` | Withdraw Money > To My Bayad Wallet > Php 300 (`asensoAccount.withdraw.amount`) > NEXT > CONFIRM, expects a success message |
| `pay_bills` | `risky` | Pay Bills from the Asenso screen, Manila Water (`payBills` data), Php 30 plus a Php 10 fee |
| `my_transactions` | none | `my transactions` opens Activity > Transaction History with at least one entry |
| `account_management` | none | Tap the avatar left of the name, open each Account Management link (InstaPay Settings, Input Distributor Code, Upload Business Permit, Terms and Conditions, Data Privacy, User Manual), check its screen, go back; FAQ is only checked as listed (it sits under the bottom edge and ignores taps) |

Notes: Add Money > Over the Counter shows "Coming soon" in the current build, so Add Money uses From My Bayad Wallet. The success receipt text of add/withdraw was not captured (no real transfer was made while writing the tests): the tests accept any "Success" message and may need that locator adjusted on the first real run. Zephyr cases are named `Asenso Account: ...` in the `Android/Asenso Account` folder.

```bash
pytest -m "device and not risky" --env qa --device emulator "tests/Android/Asenso Account"   # my transactions + account management
```

### Pay Bills test

`tests/Android/Upgraded Consumer Account/test_pay_bills.py` (marked `device` and `risky`) pays a bill for real on staging: Services > Pay Bills, wait for the billers to load, search the biller, fill the form, NEXT, CONFIRM, then it checks the "Payment Successful!" receipt. The biller, account number, nickname and amount come from `testdata/<env>.json` under `payBills` (default Manila Water, account `12358959`, nickname `Yen`, amount `30`). Each run costs the amount plus a Php 10 service fee. It logs in first, so `TEST_USERNAME` and `TEST_PASSWORD` must be set; the billers and the receipt can take up to about 60 seconds to load. Its Zephyr case is `Pay Bills: Manila Water payment shows a receipt`.

```bash
pytest -m device --env qa --device emulator "tests/Android/Upgraded Consumer Account/test_pay_bills.py"
```

### Registration tests

`tests/Android/Upgraded Consumer Account/test_registration.py` (marked `device` and `risky`) covers three scenarios, in this order:

1. **Invalid number**: `0999999999` (a leading 0 is rejected). The app shows "Invalid mobile number format" and SIGN UP! stays disabled; nothing is sent to staging.
2. **Already registered**: `9764912641`. After the OTP the app shows the login page instead of creating an account.
3. **New number** (last on purpose): needs a number that was never registered. It enters the OTP, then Complete Your Profile (name and date of birth), Create Your Password, Customize Profile (avatar and nickname), and asserts the `All set, <nickname>!` success page.

```bash
REG_MOBILE=<new 10-digit number, no leading 0> REG_PASSWORD='<9+ chars, capital, number, symbol>' \
  pytest -m device --env qa --device emulator "tests/Android/Upgraded Consumer Account/test_registration.py"
```

- `REG_MOBILE` and `REG_PASSWORD` are never stored. Without them the new-number test is skipped (the other two still run). Use a different `REG_MOBILE` every run: each run registers a real staging account, and that number cannot be used again.
- The OTP is `111111` unless `REG_OTP` is set. The code boxes are a custom widget, so the test taps the first box and presses the digit keys.
- A number cannot request a second OTP within about 2 minutes ("you still have a valid request"), which is why the new-number test runs last.
- Nickname and avatar come from `testdata/<env>.json` under `registration`: `nickname` (default `Yen`) and `avatarFile` (a file in `testdata/avatar/`, default `avatar.jpg`). Change either to use another value or picture.
- Zephyr cases: `Registration: invalid mobile number is rejected`, `Registration: already registered mobile number shows the login page` and `Registration: new mobile number completes registration`.

### Full run (unit + every device test)

```bash
export TEST_USERNAME=<10-digit mobile, no leading 0> TEST_PASSWORD=<password>
export ASENSO_USERNAME=<10-digit mobile, no leading 0> ASENSO_PASSWORD=<password>   # the Asenso account tests
# Registration test: a number never registered before, new every run. Without these only the new-number test is skipped.
export REG_MOBILE=<new 10-digit number, no leading 0> REG_PASSWORD='<9+ chars, capital, number, symbol>'   # REG_OTP optional (default 111111)
# Zephyr Scale reporting is optional (token never in a file; see "First time with Zephyr Scale"). When ZEPHYR_TOKEN is set,
# ZEPHYR_CYCLE_NAME and ZEPHYR_CASES_FOLDER are required, or the run stops before any test starts.
export ZEPHYR_TOKEN=<token> ZEPHYR_PROJECT_KEY=AMW ZEPHYR_CYCLE_NAME="<cycle name for this run>"   # a new cycle "<name> <date time>" every run
export ZEPHYR_CASES_FOLDER="<top folder for this run>"   # any name; Android/Upgraded Consumer Account, Android/Consumer Account with Asenso and Android/Asenso Account are created inside it, with the project's cases
export ARTIFACTS_DIR="$HOME/Library/CloudStorage/OneDrive-<org>/CIS/Automation Screenshots/Bayad App"   # optional, default ./artifacts
export ZEPHYR_ARTIFACTS_LINK="<shared folder URL>"                                                        # optional
emulator -avd <name>      # or connect a device; check with adb devices
appium                    # in another terminal
pytest -m "unit or device" --env qa --device emulator   # includes risky tests
```

For a full run without the money/lockout tests use `-m "unit or (device and not risky)"`. That also leaves out all registration tests, because `test_registration.py` is marked `risky`; to run only those, see "Registration tests" above.

Artifacts: `<ARTIFACTS_DIR>/Screenshots/<ZEPHYR_CASES_FOLDER>/Android/<Upgraded Consumer Account|Consumer Account with Asenso|Asenso Account>/<run date-time>/PASSED|FAILED|RECEIPT/` (the same folder tree as Zephyr: the folder you export for the run, then the project's test folders, created on demand; without `ZEPHYR_CASES_FOLDER` the first level is left out), and `<ARTIFACTS_DIR>/diagnostics/` (page source, logcat on failure).
Careful: `test_send_money.py` and `test_send_money_via_bayad_wallet.py` (same payments, entered from the Wallet tab) move real Php 10 on staging per test, `test_pay_via_qr.py` pays four QR codes (static QRs use the amount encoded in the QR) and `test_login.py` can lock the test account. `test_registration.py` registers a real staging account per run (new-number test). `test_pay_bills.py` pays Manila Water Php 30 plus a Php 10 fee per run. The `Consumer Account with Asenso` copies repeat all of this for the Asenso account, so a full run (`-m device`) pays everything twice. Both registration tests read the same `REG_MOBILE`, and a number can be registered only once, so run the two `test_registration.py` / `test_asenso_registration.py` files in separate runs with a different `REG_MOBILE` each. A full run therefore makes real payments and registers real accounts: run it only on purpose.

## Adding tests

Create a page object extending `BasePage`, put locators in the page module, delegate every interaction to `self.actions`,
and write a pytest test using the `driver` fixture with `@pytest.mark.device`. Never use `time.sleep`; use `MobileActions` waits.
A test that moves real money or sends bad logins also gets `@pytest.mark.risky`. To report it to Zephyr, add a `@pytest.mark.zephyr` marker and its case (name, objective, steps) to `framework/zephyr_cases.py`; a unit test fails if a marked test has no case definition or the other way round. The next Zephyr run creates the new case in its folder automatically. Also add a `test_asenso_*` copy in `tests/Android/Consumer Account with Asenso/` (log in with `log_in_to_home(driver, DATA, ASENSO)`, `ASENSO` from `tests/Android/helpers.py`); its Zephyr case is derived from the original automatically.

## Zephyr Scale reporting (optional)

Mark tests with `@pytest.mark.zephyr` and define their case in `framework/zephyr_cases.py`. Set `ZEPHYR_TOKEN` (never in a file). When it is set, also set:

- `ZEPHYR_CYCLE_NAME` (required): each run creates a new cycle named `<name> <date time>`.
- `ZEPHYR_CASES_FOLDER` (required, any name or `parent/child` path you choose): the top folder for the run. The project's test folders (`Android/Upgraded Consumer Account`, `Android/Consumer Account with Asenso` and `Android/Asenso Account`) are created inside it if missing, and any defined case they lack is created there.
- `ZEPHYR_PROJECT_KEY` (default `AMW`) and `ZEPHYR_ARTIFACTS_LINK` (shared screenshot folder URL, shown in the last step's actual result) are optional.

The run stops before any test starts, with the reason, if the cycle name or folder setting is missing or if creating the folder, its cases or the cycle fails (no permission, Zephyr down). Without a token the reporter does nothing. Once the tests are running, a result that cannot be published only logs a warning and never changes a test result.
At the start of a run every case in the folder is listed as *Not Executed*; each test that runs updates its case to Pass / Fail / Blocked. Each step of the case gets its own actual result: on a pass, what that step expected (e.g. `The Welcome screen is displayed`); on a failure, the failure text goes on the step it belongs to (found from the assertion message, else the last step), the steps before it pass and the steps after it are *Not Executed*; the screenshot link is added to that step. A test reports only to the case with its name in the folder.
At the end of the pytest output a `Zephyr` line shows what the run did, for example:
`Zephyr: folder 'Sprint 42 regression' (created, 20 cases created, 20 in total) | cycle AMW-R210 'Regression 2026-10-19 17:30' | results: 3 Pass`.
`python scripts/create_zephyr_cases.py` creates the defined cases in a folder by hand (`--dry-run` first).
