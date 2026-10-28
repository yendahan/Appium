# OTP Sending Money

Checks the transaction OTP ("TOP trigger") from `TOP_Instapay_Bayad_Wallet_Test_Scenarios.xlsx`. It is isolated: it runs **only** when this
folder is named on the command line, never as part of `tests` or `tests/Android` runs.

WARNING: all six tests complete real sends on staging, about Php 66,000 in total (Php 6,000 To Other Banks, Php 60,000 To Bayad Wallet).
The account must be an Upgraded account funded with enough balance (at least Php 20,000.01 for each wallet test).

## Variables (never saved to a file)

| Variable | Required | Meaning |
|---|---|---|
| `OTP_MOBILE` | yes | Mobile number of the sending account (10 digits). Must not be the recipient wallet number (`sendMoney.bayadWalletNumber.asenso` in `testdata/qa.json`) |
| `OTP_PASSWORD` | yes | Its password |
| `OTP_CODE` | no | The OTP to enter. Default `111111` |

The Other Banks recipient is `sendMoney.otherBank` in `testdata/qa.json`; the amounts are the `otpSend` node.

## Run

```
export OTP_MOBILE=9xxxxxxxxx OTP_PASSWORD='...'
pytest -m device --env qa --device emulator "tests/Android/OTP Sending Money" -v -rs --tb=short
```

One scenario: add `-k top_02` (or `bw_03`, and so on). Add `--reuse-app` to share one login between the six tests.

## Scenarios

| Test | Type | Amount (Php) | Expected |
|---|---|---|---|
| `test_top_01_below_trigger_other_bank` | Other Banks | 1,999.99 | No OTP; send completes |
| `test_top_02_at_trigger_other_bank` | Other Banks | 2,000 | OTP shows; enter it; send completes |
| `test_top_03_above_trigger_other_bank` | Other Banks | 2,000.01 | OTP shows; enter it; send completes |
| `test_bw_01_below_trigger_wallet` | Bayad Wallet | 19,999.99 | No OTP; send completes |
| `test_bw_02_at_trigger_wallet` | Bayad Wallet | 20,000 | OTP shows; enter it; send completes |
| `test_bw_03_above_trigger_wallet` | Bayad Wallet | 20,000.01 | OTP shows; enter it; send completes |

The OTP screen is recognised by its "Verification Code" title (the same screen as the registration OTP). The tests tap CONFIRM, then look for
it. If the app asks for the OTP at another point (for example after NEXT), report it and the page object will be adjusted.

Screenshots: `artifacts/Screenshots/Android/OTP Sending Money/<run date-time>/` (the OTP screen in `PASSED`, each receipt in `RECEIPT`).
