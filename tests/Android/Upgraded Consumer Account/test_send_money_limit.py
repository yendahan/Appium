"""WARNING: the To Bayad Wallet test taps CONFIRM with Php 50,000; it only fails safely while the wallet holds less than that.

Sends Php 50,000 (more than the wallet balance) and expects the Insufficient Funds popup, then PROCEED TO ADD MONEY."""
import pytest

from framework.test_data_loader import TestDataLoader
from pages.send_money_page import SendMoneyPage
from tests.Android.helpers import log_in_to_home

pytestmark = [pytest.mark.device, pytest.mark.risky, pytest.mark.shared_session("credentials")]

REVIEW_TIMEOUT = 60
POPUP_TIMEOUT = 30
DATA = TestDataLoader.for_current_env()


@pytest.fixture
def send_money(driver) -> SendMoneyPage:
    log_in_to_home(driver, DATA)
    return SendMoneyPage(driver).open()


def assert_prompts_add_money(page: SendMoneyPage, name: str) -> None:
    assert page.is_insufficient_funds_displayed(POPUP_TIMEOUT), "Insufficient Funds popup should show for Php 50,000"
    page.actions.screenshot(f"{name}-insufficientFunds", "PASSED")
    page.proceed_to_add_money()
    assert page.is_add_money_displayed(POPUP_TIMEOUT), "PROCEED TO ADD MONEY should open the Add Money screen"
    page.actions.screenshot(f"{name}-addMoney", "PASSED")


@pytest.mark.zephyr
def test_to_bayad_wallet_over_limit(send_money):
    """Negative: sending Php 50,000 to a Bayad Wallet is refused after CONFIRM and prompts to add money."""
    send = DATA.node("sendMoney")
    send_money.to_bayad_wallet(send["bayadWalletNumber"]["asenso"], send["breachAmount"])
    assert send_money.is_review_displayed(REVIEW_TIMEOUT), "Php 50,000 should reach the review step"
    send_money.confirm()
    assert_prompts_add_money(send_money, "toBayadWallet")


@pytest.mark.zephyr
def test_to_other_bank_over_limit(send_money):
    """Negative: sending Php 50,000 to another bank is refused after NEXT and prompts to add money."""
    send = DATA.node("sendMoney")
    bank = send["otherBank"]
    send_money.to_other_bank(bank["accountNumber"], bank["accountName"], bank["bankName"], send["breachAmount"])
    assert_prompts_add_money(send_money, "toOtherBank")
