"""WARNING: taps CONFIRM and moves real Php 10 on staging per test (six per run)."""
from pathlib import Path

import pytest

from framework.test_data_loader import TestDataLoader
from pages.send_money_page import SendMoneyPage
from tests.Android.helpers import ASENSO, log_in_to_home

pytestmark = [pytest.mark.device, pytest.mark.risky]

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
    log_in_to_home(driver, DATA, ASENSO)
    return SendMoneyPage(driver).open()


def complete_transaction(page: SendMoneyPage, receipt_name: str) -> None:
    page.confirm()
    sent = page.is_receipt_displayed(COMPLETE_TIMEOUT)
    page.actions.screenshot(receipt_name, "RECEIPT")
    assert not (not sent and page.is_in_progress_displayed()), \
        "Receipt shows 'Send Money in Progress!' instead of 'Successfully Sent!'"
    assert sent, "Receipt should show 'Successfully Sent!' after CONFIRM"


@pytest.mark.zephyr
@pytest.mark.parametrize("qr_type,key", QR_CASES, ids=[c[0] for c in QR_CASES])
def test_via_qr_valid(send_money, qr_type, key):
    """Positive: Via QR accepts a valid QR code."""
    send = DATA.node("sendMoney")
    send_money.via_qr(ROOT / send["qr"][key], send["amount"])
    assert send_money.is_review_displayed(REVIEW_TIMEOUT), f"{qr_type} should reach the review step"
    complete_transaction(send_money, f"viaQr-{qr_type}")


@pytest.mark.zephyr
def test_to_bayad_wallet_valid(send_money):
    """Positive: To Bayad Wallet accepts a valid registered number."""
    send = DATA.node("sendMoney")
    send_money.to_bayad_wallet(send["bayadWalletNumber"]["upgraded"], send["amount"])
    assert send_money.is_review_displayed(REVIEW_TIMEOUT), "Valid wallet number should reach the review step"
    complete_transaction(send_money, "toBayadWallet")


@pytest.mark.zephyr
def test_to_other_bank_valid(send_money):
    """Positive: To Other Banks and E-Wallets accepts a valid Philippine National Bank account."""
    send = DATA.node("sendMoney")
    bank = send["otherBank"]
    send_money.to_other_bank(bank["accountNumber"], bank["accountName"], bank["bankName"], send["amount"])
    assert send_money.is_review_displayed(REVIEW_TIMEOUT), "Valid bank account should reach the review step"
    complete_transaction(send_money, "toOtherBank")
