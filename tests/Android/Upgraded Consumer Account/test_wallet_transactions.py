import pytest

from framework.test_data_loader import TestDataLoader
from pages.activity_page import ActivityPage
from tests.Android.helpers import log_in_to_home

pytestmark = pytest.mark.device

SCREEN_TIMEOUT = 30
DATA = TestDataLoader.for_current_env()


@pytest.fixture
def activity(driver) -> ActivityPage:
    log_in_to_home(driver, DATA)
    page = ActivityPage(driver).open_from_wallet()
    assert page.is_displayed(SCREEN_TIMEOUT), "Wallet > See all should show the Activity page"
    return page


@pytest.mark.zephyr
def test_wallet_transaction_history(activity):
    """Positive: Wallet > See all opens Activity; Transaction History shows its list or the empty message."""
    assert activity.show_transaction_history(), "Transaction History should show its list or the empty message"
    activity.actions.screenshot("walletTransactionHistory", "PASSED")


@pytest.mark.zephyr
def test_wallet_ongoing_activities(activity):
    """Positive: Wallet > See all opens Activity; Ongoing Activities shows its list or the empty message."""
    assert activity.show_ongoing_activities(), "Ongoing Activities should show its list or the empty message"
    activity.actions.screenshot("walletOngoingActivities", "PASSED")
