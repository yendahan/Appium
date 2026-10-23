import pytest

from framework.test_data_loader import TestDataLoader
from pages.asenso_page import AsensoPage
from tests.Android.helpers import ASENSO, log_in_to_home

pytestmark = [pytest.mark.device, pytest.mark.shared_session(ASENSO)]

SCREEN_TIMEOUT = 30
DATA = TestDataLoader.for_current_env()

# (link, heading of the screen it opens). FAQ sits under the bottom edge and ignores taps, so it is only checked as shown.
LINKS = [
    ("InstaPay Settings", "InstaPay Settings"),
    ("Input Distributor Code", "Input Distributor Code"),
    ("Upload Business Permit", "Upload New Business Permit"),
    ("Terms and Conditions", "Terms and Conditions"),
    ("Data Privacy", "Data Privacy"),
    ("User Manual", "User Manual"),
]


@pytest.fixture
def account_management(driver) -> AsensoPage:
    log_in_to_home(driver, DATA, ASENSO)
    page = AsensoPage(driver).open().open_account_management()
    assert page.is_account_management_displayed(SCREEN_TIMEOUT), "Account Management should show after tapping the avatar"
    return page


@pytest.mark.zephyr
def test_account_management_links_open_their_screens(account_management):
    """Positive: every Account Management link opens its screen and Back returns to the list."""
    for link, heading in LINKS:
        assert account_management.is_link_displayed(link, SCREEN_TIMEOUT), f"'{link}' link should be listed"
        account_management.open_link(link)
        assert account_management.is_heading_displayed(heading, SCREEN_TIMEOUT), f"'{link}' should open '{heading}'"
        assert account_management.is_link_content_displayed(link, SCREEN_TIMEOUT), f"'{link}' should finish loading"
        account_management.actions.screenshot(f"asensoAccountManagement-{link}", "PASSED")
        assert account_management.back_to_account_management(), f"Back from '{link}' should return to Account Management"
    account_management.actions.swipe("up")  # on a taller screen the list runs past the bottom edge: scroll FAQ into view
    assert account_management.is_link_displayed("FAQ"), "'FAQ' link should be listed"
