"""WARNING: taps CONFIRM and moves real Php 300 from the Bayad Wallet to the Asenso Wallet on staging per run."""
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
def test_add_money_from_bayad_wallet(asenso):
    """Positive: Add Money from My Bayad Wallet accepts Php 300 and shows a success receipt after CONFIRM."""
    asenso.add_money_from_wallet(DATA.node("asensoAccount")["addMoney"]["amount"])
    assert asenso.is_confirmation_displayed(CONFIRMATION_TIMEOUT), "Transaction Confirmation should show after NEXT"
    asenso.confirm()
    added = asenso.is_success_displayed(COMPLETE_TIMEOUT)
    asenso.actions.screenshot("asensoAddMoney", "RECEIPT")
    assert added, "Receipt should show a success message after CONFIRM"
