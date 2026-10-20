"""WARNING: sends wrong passwords and can lock the test accounts ("blocked temporarily")."""
import pytest

from framework.test_data_loader import TestDataLoader
from pages.home_page import HomePage
from pages.login_page import LoginPage
from pages.privacy_notice_page import PrivacyNoticePage

pytestmark = [pytest.mark.device, pytest.mark.risky]

LOGIN_TIMEOUT = 60
ERROR_TIMEOUT = 30
NEGATIVE_TIMEOUT = 3


@pytest.fixture(scope="module")
def data():
    return TestDataLoader.for_current_env()


@pytest.fixture
def login_page(driver) -> LoginPage:
    notice = PrivacyNoticePage(driver)
    assert notice.is_displayed(), "Privacy notice should be the first screen of a fresh session"
    page = notice.accept_and_continue().go_to_login()
    assert page.is_displayed(), "Login form should be displayed"
    return page


@pytest.mark.zephyr
def test_valid_credentials_reach_home(driver, login_page, data):
    """Positive: valid credentials reach the home screen."""
    creds = data.node("asensoCredentials")
    login_page.login_as(creds["username"], creds["password"])
    biometric = login_page.expect_biometric_setup()
    assert biometric.is_displayed(LOGIN_TIMEOUT), "Biometric setup is offered after first login"
    assert biometric.skip().is_displayed(LOGIN_TIMEOUT), "Home screen should show after skipping biometrics"


@pytest.mark.zephyr
def test_unknown_account_is_rejected(driver, login_page, data):
    """Negative: unknown account is rejected with an error and can be retried."""
    bad = data.node("invalidLogin")
    login_page.login_as(bad["username"], bad["password"])
    assert login_page.is_invalid_credentials_error_shown(ERROR_TIMEOUT), \
        f"Expected '{LoginPage.INVALID_CREDENTIALS_MESSAGE}'"
    assert login_page.dismiss_error().is_displayed(), "TRY AGAIN should return to the login form"
    assert not HomePage(driver).is_displayed(NEGATIVE_TIMEOUT), "Must not reach home"


@pytest.mark.zephyr
def test_wrong_password_is_rejected(driver, login_page, data):
    """Negative: valid username with a wrong password never reaches home."""
    creds = data.node("asensoCredentials")
    login_page.login_as(creds["username"], data.node("invalidLogin")["password"])
    assert login_page.is_invalid_credentials_error_shown(ERROR_TIMEOUT)
    assert not HomePage(driver).is_displayed(NEGATIVE_TIMEOUT)


@pytest.mark.zephyr
def test_submit_is_disabled_until_both_fields_are_filled(driver, login_page, data):
    """Edge: LOG IN stays disabled for an empty form and for a half-filled form."""
    assert not login_page.is_submit_enabled(), "Empty form must not be submittable"
    login_page.enter_mobile(data.node("invalidLogin")["username"])
    assert not login_page.is_submit_enabled(), "Mobile only must not be submittable"
    assert not HomePage(driver).is_displayed(NEGATIVE_TIMEOUT)


@pytest.mark.zephyr
def test_mobile_field_is_limited_to_ten_characters(driver, login_page, data):
    """Boundary: the mobile field keeps at most 10 characters."""
    eleven = data.node("boundary")["elevenDigitMobile"]
    login_page.enter_mobile(eleven)
    assert login_page.mobile_field_text() == eleven[:10]
