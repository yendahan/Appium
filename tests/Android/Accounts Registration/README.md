# Accounts Registration

Registers new accounts on staging and upgrades each one (Upgrade Account wizard, with the emulator camera). It is isolated: it runs **only**
when this folder is named on the command line, never as part of `tests` or `tests/Android` runs.

WARNING: every run creates real staging accounts. Use a number that has not been used.

## Before you run

- Appium server on :4723 and an emulator started (`adb devices` shows it).
- Run everything in **one terminal**, from the project root, with the virtualenv active.

## Variables (never saved to a file)

| Variable | Required | Meaning |
|---|---|---|
| `REG_MOBILE` | yes | First number to try (10 digits, e.g. `9103221161`). A number that is already registered is skipped and the next one (+1) is tried, up to 20 in a row |
| `REG_PASSWORD` | yes | Password for every new account (9+ chars, a capital, a number, a symbol, no repeats or sequences) |
| `REG_COUNT` | no | How many accounts to create. Default **1** |
| `REG_OTP` | no | Verification code. Default `111111` |

## Run

```
export REG_COUNT=3 REG_MOBILE=9103221161 REG_PASSWORD='Bayad@2026'
pytest -m device --env qa --device emulator "tests/Android/Accounts Registration" -v -rs --tb=short
```

The run has `REG_COUNT` registration tests (`test_register_account[account-1..N]`) followed by `REG_COUNT` upgrade tests
(`test_upgrade_account[account-1..N]`). Each registration takes the next free number after the previous one; each upgrade logs in
with the number its registration created. Each test uses a fresh app session.

Add `-o log_cli=true -o log_cli_level=INFO` to see the numbers as they are registered ("Registered account 1 of 3: 9103221161").
Run only the registration with `-k test_register_account`. An upgrade is skipped if its registration did not complete.

## Check the count before a real run

```
echo $REG_COUNT
pytest -m device --env qa --device emulator "tests/Android/Accounts Registration" --collect-only -q | tail -3
```

With `REG_COUNT=3` the last line says `6 tests collected` (3 registrations + 3 upgrades). `2 tests collected` means `REG_COUNT` did not
reach pytest: set it with `export`, or on the same line in front of `pytest`, in the same terminal and without a line break in the command.

## After the run

- Screenshots: `artifacts/Screenshots/Android/Accounts Registration/<run date-time>/PASSED|FAILED`, the upgrade ones named with the number.
- The numbers used are listed in `artifacts/Accounts Registration/registered_accounts.txt`, updated by the tests (numbers only): under "upgraded" once the upgrade is submitted, else under "registered".
- If an upgrade fails midway, the account stays registered with its progress saved, so a number can be upgraded only once.
