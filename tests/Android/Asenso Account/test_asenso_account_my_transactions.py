import pytest

from framework.test_data_loader import TestDataLoader
from pages.asenso_page import AsensoPage
from tests.Android.helpers import ASENSO, log_in_to_home

pytestmark = [pytest.mark.device, pytest.mark.shared_session(ASENSO)]

HISTORY_TIMEOUT = 30
DATA = TestDataLoader.for_current_env()


@pytest.fixture
def asenso(driver) -> AsensoPage:
    log_in_to_home(driver, DATA, ASENSO)
    return AsensoPage(driver).open()


@pytest.mark.zephyr
def test_my_transactions_shows_history(asenso):
    """Positive: my transactions opens the Activity screen on its Transaction History tab, with entries."""
    asenso.open_my_transactions()
    assert asenso.is_transaction_history_displayed(HISTORY_TIMEOUT), "Activity > Transaction History should show"
    assert asenso.transaction_rows(), "Transaction History should list at least one transaction"
    asenso.actions.screenshot("asensoMyTransactions", "PASSED")
