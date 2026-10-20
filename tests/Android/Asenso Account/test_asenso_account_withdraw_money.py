"""WARNING: taps CONFIRM and moves real Php 300 from the Asenso Wallet to the Bayad Wallet on staging per run."""
import pytest

from framework.test_data_loader import TestDataLoader
from pages.asenso_page import AsensoPage
from tests.Android.helpers import ASENSO, log_in_to_home

pytestmark = [pytest.mark.device, pytest.mark.risky]

CONFIRMATION_TIMEOUT = 60
COMPLETE_TIMEOUT = 60
DATA = TestDataLoader.for_current_env()


@pytest.fixture
def asenso(driver) -> AsensoPage:
    log_in_to_home(driver, DATA, ASENSO)
    return AsensoPage(driver).open()


@pytest.mark.zephyr
def test_withdraw_money_to_bayad_wallet(asenso):
    """Positive: Withdraw Money to My Bayad Wallet accepts Php 300 and shows a success receipt after CONFIRM."""
    asenso.withdraw_to_wallet(DATA.node("asensoAccount")["withdraw"]["amount"])
    assert asenso.is_confirmation_displayed(CONFIRMATION_TIMEOUT), "Transaction Confirmation should show after NEXT"
    asenso.confirm()
    withdrawn = asenso.is_success_displayed(COMPLETE_TIMEOUT)
    asenso.actions.screenshot("asensoWithdrawMoney", "RECEIPT")
    assert withdrawn, "Receipt should show a success message after CONFIRM"
