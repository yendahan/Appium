import pytest

from framework.test_data_loader import TestDataLoader
from pages.activity_page import ActivityPage
from tests.Android.helpers import BASIC, log_in_to_home

pytestmark = pytest.mark.device

SCREEN_TIMEOUT = 30
DATA = TestDataLoader.for_current_env()


@pytest.mark.zephyr
def test_transaction_history_and_ongoing_activities_screenshots(driver):
    """Positive: Activity shows Transaction History and Ongoing Activities; a screenshot is saved of each."""
    log_in_to_home(driver, DATA, BASIC)
    activity = ActivityPage(driver).open()
    assert activity.is_displayed(SCREEN_TIMEOUT), "Activity should show its Transaction History and Ongoing Activities tabs"
    assert activity.show_transaction_history(), "Transaction History should show its list or the empty message"
    activity.actions.screenshot("basicTransactionHistory", "PASSED")
    assert activity.show_ongoing_activities(), "Ongoing Activities should show its list or the empty message"
    activity.actions.screenshot("basicOngoingActivities", "PASSED")
