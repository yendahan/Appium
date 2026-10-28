"""WARNING: the Php 300 test taps CONFIRM and requests a real cash-in on staging per run; it needs a Basic account under its wallet limit."""
import pytest

from framework.test_data_loader import TestDataLoader
from pages.add_money_page import AddMoneyPage
from tests.Android.helpers import BASIC, log_in_to_home

pytestmark = [pytest.mark.device, pytest.mark.shared_session(BASIC)]

CONFIRMATION_TIMEOUT = 60
COMPLETE_TIMEOUT = 60
ERROR_TIMEOUT = 10
NEGATIVE_TIMEOUT = 3
DATA = TestDataLoader.for_current_env()


@pytest.fixture
def add_money(driver) -> AddMoneyPage:
    log_in_to_home(driver, DATA, BASIC)
    return AddMoneyPage(driver).open()


@pytest.mark.zephyr
@pytest.mark.risky
def test_over_the_counter_accepts_the_minimum_amount(add_money):
    """Positive: Over the Counter (Bayad Center) accepts Php 300, reaches Payment Confirmation and shows a success receipt after CONFIRM."""
    amount = DATA.node("basicAccount")["addMoney"]["amount"]
    add_money.enter_amount(amount).next()
    assert add_money.is_confirmation_displayed(CONFIRMATION_TIMEOUT), "Payment Confirmation should show after NEXT"
    add_money.actions.screenshot("basicAddMoney-overTheCounter", "PASSED")
    add_money.confirm()
    added = add_money.is_success_displayed(COMPLETE_TIMEOUT)
    add_money.actions.screenshot("basicAddMoney-overTheCounter-confirmed", "RECEIPT" if added else "FAILED")
    assert added, "Receipt should show a success message after CONFIRM (any other screen, such as the wallet limit error, fails the test)"


@pytest.mark.zephyr
def test_over_the_counter_below_minimum_shows_an_error(add_money):
    """Negative: an amount under the minimum shows the minimum cash-in error and cannot be submitted."""
    below = DATA.node("basicAccount")["addMoney"]["belowMinimum"]
    add_money.enter_amount(below)
    assert add_money.is_minimum_error_displayed(ERROR_TIMEOUT), "The minimum cash-in error should show for a small amount"
    add_money.actions.screenshot("basicAddMoney-belowMinimum", "PASSED")
    assert not add_money.next_is_enabled(), "NEXT must stay disabled below the minimum"
