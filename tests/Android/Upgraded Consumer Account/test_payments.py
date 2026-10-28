"""WARNING: taps CONFIRM and moves real money on staging: Send Money from Services (six payments), Send Money from the Wallet tab (six more) and
Pay via QR (four), per run.

Run all three groups with one command: pytest -m device --reuse-app "tests/Android/Upgraded Consumer Account/test_payments.py" (or `-k pay_via_qr` /
`-k via_qr_valid` style filters inside it). Static QR codes pay the amount encoded in the QR (e.g. Php 88.88); every other test pays Php 10."""
from pathlib import Path

import pytest

from framework.test_data_loader import TestDataLoader
from pages.pay_via_qr_page import PayViaQrPage
from pages.send_money_page import SendMoneyPage
from tests.Android.helpers import log_in_to_home

pytestmark = [pytest.mark.device, pytest.mark.risky]
# The Send Money tests keep one logged-in app with --reuse-app (they leave the receipt through DONE); Pay via QR keeps a fresh app.
SHARED = pytest.mark.shared_session("credentials")

REVIEW_TIMEOUT = 60
COMPLETE_TIMEOUT = 90  # InstaPay transfers take 45s+
ROOT = Path(__file__).resolve().parents[3]
DATA = TestDataLoader.for_current_env()

QR_CASES = [
    ("QRP2P - Static", "p2pStatic"),
    ("QRP2P - Dynamic", "p2pDynamic"),
    ("QRP2M - Static", "p2mStatic"),
    ("QRP2M - Dynamic", "p2mDynamic"),
]


@pytest.fixture
def send_money(driver) -> SendMoneyPage:
    log_in_to_home(driver, DATA)
    return SendMoneyPage(driver).open()


@pytest.fixture
def wallet_send(driver) -> SendMoneyPage:
    log_in_to_home(driver, DATA)
    return SendMoneyPage(driver).open_from_wallet()


@pytest.fixture
def pay_via_qr(driver) -> PayViaQrPage:
    log_in_to_home(driver, DATA)
    return PayViaQrPage(driver).open()


def complete_transaction(page: SendMoneyPage, receipt_name: str) -> None:
    page.confirm()
    sent = page.is_receipt_displayed(COMPLETE_TIMEOUT)
    page.actions.screenshot(receipt_name, "RECEIPT")
    assert not (not sent and page.is_in_progress_displayed()), \
        "Receipt shows 'Send Money in Progress!' instead of 'Successfully Sent!'"
    assert sent, "Receipt should show 'Successfully Sent!' after CONFIRM"


# --- Send Money from Services -------------------------------------------------------------------------------------------
@SHARED
@pytest.mark.zephyr
@pytest.mark.parametrize("qr_type,key", QR_CASES, ids=[c[0] for c in QR_CASES])
def test_via_qr_valid(send_money, qr_type, key):
    """Positive: Via QR accepts a valid QR code."""
    send = DATA.node("sendMoney")
    send_money.via_qr(ROOT / send["qr"][key], send["amount"])
    assert send_money.is_review_displayed(REVIEW_TIMEOUT), f"{qr_type} should reach the review step"
    complete_transaction(send_money, f"viaQr-{qr_type}")


@SHARED
@pytest.mark.zephyr
def test_to_bayad_wallet_valid(send_money):
    """Positive: To Bayad Wallet accepts a valid registered number."""
    send = DATA.node("sendMoney")
    send_money.to_bayad_wallet(send["bayadWalletNumber"]["asenso"], send["amount"])
    assert send_money.is_review_displayed(REVIEW_TIMEOUT), "Valid wallet number should reach the review step"
    complete_transaction(send_money, "toBayadWallet")


@SHARED
@pytest.mark.zephyr
def test_to_other_bank_valid(send_money):
    """Positive: To Other Banks and E-Wallets accepts a valid account."""
    send = DATA.node("sendMoney")
    bank = send["otherBank"]
    send_money.to_other_bank(bank["accountNumber"], bank["accountName"], bank["bankName"], send["amount"])
    assert send_money.is_review_displayed(REVIEW_TIMEOUT), "Valid bank account should reach the review step"
    complete_transaction(send_money, "toOtherBank")


# --- Send Money from the Wallet tab -------------------------------------------------------------------------------------
@SHARED
@pytest.mark.zephyr
@pytest.mark.parametrize("qr_type,key", QR_CASES, ids=[c[0] for c in QR_CASES])
def test_wallet_via_qr_valid(wallet_send, qr_type, key):
    """Positive: Via QR accepts a valid QR code."""
    send = DATA.node("sendMoney")
    wallet_send.via_qr(ROOT / send["qr"][key], send["amount"])
    assert wallet_send.is_review_displayed(REVIEW_TIMEOUT), f"{qr_type} should reach the review step"
    complete_transaction(wallet_send, f"wallet-viaQr-{qr_type}")


@SHARED
@pytest.mark.zephyr
def test_wallet_to_bayad_wallet_valid(wallet_send):
    """Positive: To Bayad Wallet accepts a valid registered number."""
    send = DATA.node("sendMoney")
    wallet_send.to_bayad_wallet(send["bayadWalletNumber"]["asenso"], send["amount"])
    assert wallet_send.is_review_displayed(REVIEW_TIMEOUT), "Valid wallet number should reach the review step"
    complete_transaction(wallet_send, "wallet-toBayadWallet")


@SHARED
@pytest.mark.zephyr
def test_wallet_to_other_bank_valid(wallet_send):
    """Positive: To Other Banks and E-Wallets accepts a valid account."""
    send = DATA.node("sendMoney")
    bank = send["otherBank"]
    wallet_send.to_other_bank(bank["accountNumber"], bank["accountName"], bank["bankName"], send["amount"])
    assert wallet_send.is_review_displayed(REVIEW_TIMEOUT), "Valid bank account should reach the review step"
    complete_transaction(wallet_send, "wallet-toOtherBank")


# --- Pay via QR ---------------------------------------------------------------------------------------------------------
@pytest.mark.zephyr
@pytest.mark.parametrize("qr_type,key", QR_CASES, ids=[c[0] for c in QR_CASES])
def test_pay_via_qr_valid(pay_via_qr, qr_type, key):
    """Positive: Pay via QR accepts a valid QR code scanned from the gallery."""
    send = DATA.node("sendMoney")
    pay_via_qr.pay(ROOT / send["qr"][key], send["amount"])
    assert pay_via_qr.is_review_displayed(REVIEW_TIMEOUT), f"{qr_type} should reach the review step"
    pay_via_qr.confirm()
    paid = pay_via_qr.is_receipt_displayed(COMPLETE_TIMEOUT)
    pay_via_qr.actions.screenshot(f"payViaQr-{qr_type}", "RECEIPT")
    assert paid, "Receipt should show 'Successfully Sent!' (or 'Send Money in Progress!') after CONFIRM"
