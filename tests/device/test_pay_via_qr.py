"""WARNING: taps CONFIRM and moves real money on staging per test (four per run).

Static QR codes carry their own amount (e.g. Php 88.88); only dynamic QR codes use the test-data amount."""
from pathlib import Path

import pytest

from framework.test_data_loader import TestDataLoader
from pages.pay_via_qr_page import PayViaQrPage
from tests.device.helpers import log_in_to_home

pytestmark = [pytest.mark.device, pytest.mark.risky]

REVIEW_TIMEOUT = 20
COMPLETE_TIMEOUT = 30
ROOT = Path(__file__).resolve().parents[2]
DATA = TestDataLoader.for_current_env()

QR_CASES = [
    ("QRP2P - Static", "p2pStatic"),
    ("QRP2P - Dynamic", "p2pDynamic"),
    ("QRP2M - Static", "p2mStatic"),
    ("QRP2M - Dynamic", "p2mDynamic"),
]


@pytest.fixture
def pay_via_qr(driver) -> PayViaQrPage:
    log_in_to_home(driver, DATA)
    return PayViaQrPage(driver).open()


@pytest.mark.parametrize("qr_type,key", QR_CASES, ids=[c[0] for c in QR_CASES])
def test_pay_via_qr_valid(pay_via_qr, qr_type, key):
    """Positive: Pay via QR accepts a valid QR code scanned from the gallery."""
    send = DATA.node("sendMoney")
    pay_via_qr.pay(ROOT / send["qr"][key], send["amount"])
    assert pay_via_qr.is_review_displayed(REVIEW_TIMEOUT), f"{qr_type} should reach the review step"
    pay_via_qr.confirm()
    paid = pay_via_qr.is_receipt_displayed(COMPLETE_TIMEOUT)
    pay_via_qr.actions.screenshot(f"payViaQr-{qr_type}", "RECEIPT")
    assert paid, "Receipt should show 'Successfully Sent!' after CONFIRM"
