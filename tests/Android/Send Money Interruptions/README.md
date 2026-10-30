# Send Money interruptions

Interrupts the Send Money flow (app to background, rotation, device lock, app killed, Back key, network loss) and checks the app recovers.
This folder runs only when named on the command line (conftest `ISOLATED_FOLDERS`), never with `pytest`, `tests` or `tests/Android`:

```
pytest -m device "tests/Android/Send Money Interruptions" --env qa --device emulator
```

Files: `test_send_money_bayadtobayad_interruptions.py` (To Bayad Wallet, INT-01..13) and `test_send_money_to_instapay_interruptions.py` (To Other Banks, Via QR and Pay via QR, FLOW-01..07 per flow; the after-CONFIRM ones, FLOW-05..07, send a real Php 10 each with a dynamic QR). Shared helpers: `tests/Android/interruption_helpers.py`.

INT-01 to INT-09 stop before CONFIRM, so no money moves. INT-10 to INT-13 (marked `risky`) tap CONFIRM and send a real Php 10 each (INT-12 sends nothing when the network popup shows). They use the Upgraded account (`TEST_USERNAME` / `TEST_PASSWORD`) and send Php 10 to the Asenso wallet number.
The app is portrait-only (MainActivity requests it), so the rotation tests expect the device to refuse the rotation. Offline, the app shows an "Oops! ... check your internet" popup (OK, GOT IT) and returns to the Send Money form.
Network loss and lock/unlock use Appium driver commands (`mobile: setConnectivity`, `lock`/`unlock`); they need an emulator. A failed network test turns the network back on in its `finally`.
Not covered: incoming call/SMS and low battery (need local `adb emu` calls).
