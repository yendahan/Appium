"""WARNING: taps CONFIRM and pays real money on staging (Php 30 plus a Php 10 fee) per run."""
import pytest

from framework.test_data_loader import TestDataLoader
from pages.asenso_page import AsensoPage
from pages.pay_bills_page import PayBillsPage
from tests.Android.helpers import ASENSO, log_in_to_home

pytestmark = [pytest.mark.device, pytest.mark.risky]

REVIEW_TIMEOUT = 60  # the review screen loads after NEXT
COMPLETE_TIMEOUT = 60  # payment takes up to ~30s
DIALOG_TIMEOUT = 5  # the Customer E-Receipt dialog is already up when the receipt is detected
DATA = TestDataLoader.for_current_env()


@pytest.fixture
def pay_bills(driver) -> PayBillsPage:
    log_in_to_home(driver, DATA, ASENSO)
    AsensoPage(driver).open().open_pay_bills()
    return PayBillsPage(driver).wait_for_billers()


@pytest.mark.zephyr
def test_asenso_pay_bills_manila_water(pay_bills):
    """Positive: Pay Bills from the Asenso screen accepts a valid Manila Water account and shows a receipt."""
    bill = DATA.node("payBills")
    pay_bills.pay(bill["biller"], bill["accountNumber"], bill["nickname"], bill["amount"], tap_search=True)
    assert pay_bills.is_review_displayed(REVIEW_TIMEOUT), "Payment Summary should show after NEXT"
    pay_bills.confirm()
    assert pay_bills.is_receipt_displayed(COMPLETE_TIMEOUT), "Receipt (or the Customer E-Receipt dialog) should show after CONFIRM"
    if pay_bills.is_e_receipt_displayed(DIALOG_TIMEOUT):
        pay_bills.actions.screenshot("asensoPayBills-manilaWater-eReceipt", "RECEIPT")
        pay_bills.dismiss_e_receipt()
    paid = pay_bills.is_payment_successful_displayed(COMPLETE_TIMEOUT)
    pay_bills.actions.screenshot("asensoPayBills-manilaWater", "RECEIPT")
    assert paid, "Receipt should show 'Payment Successful!' after CONFIRM"
