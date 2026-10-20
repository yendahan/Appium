"""WARNING: the new-number test registers a real account on staging per run.

Supply that number every run (never stored): REG_MOBILE=9100000001 pytest -m device "tests/Android/Consumer Account with Asenso/test_asenso_registration.py"
REG_PASSWORD is also required. REG_OTP overrides the default test OTP. The new-number test is last on purpose: requesting a second OTP for the
same number within ~2 minutes shows "you still have a valid request"."""
import os
from pathlib import Path

import pytest

from framework.test_data_loader import TestDataLoader
from pages.login_page import LoginPage
from pages.privacy_notice_page import PrivacyNoticePage
from pages.profile_page import ProfilePage
from pages.verification_page import VerificationPage

pytestmark = [pytest.mark.device, pytest.mark.risky]

AVATAR_DIR = Path(__file__).resolve().parents[3] / "testdata" / "avatar"
DEFAULT_OTP = "111111"
REGISTERED_NUMBER = "9764912641"
INVALID_NUMBER = "0999999999"
VERIFICATION_TIMEOUT = 60
ERROR_TIMEOUT = 30
NEGATIVE_TIMEOUT = 3
PROFILE_TIMEOUT = 60
PASSWORD_TIMEOUT = 60
SUCCESS_TIMEOUT = 60  # account creation after SUBMIT takes ~15s
FIRST_NAME, LAST_NAME = "Test", "Automation"
BIRTH_YEAR, BIRTH_DAY = 1990, 15
LOGIN_TIMEOUT = 60


@pytest.fixture(scope="module")
def registration_mobile() -> str:
    mobile = os.environ.get("REG_MOBILE", "").strip()
    if not mobile:
        pytest.skip("set REG_MOBILE (e.g. 9100000001) to run the registration test")
    return mobile


@pytest.fixture(scope="module")
def registration_password() -> str:
    password = os.environ.get("REG_PASSWORD", "")
    if not password:
        pytest.skip("set REG_PASSWORD (9+ chars, capital, number, symbol, no repeats or sequences)")
    return password


@pytest.fixture(scope="module")
def profile_data() -> dict:
    return TestDataLoader.for_current_env().node("registration")


@pytest.fixture(scope="module")
def registration_otp() -> str:
    return os.environ.get("REG_OTP", "").strip() or DEFAULT_OTP


@pytest.mark.zephyr
def test_invalid_mobile_number_is_rejected(driver):
    """Negative: a number starting with 0 shows the format error and cannot be submitted."""
    welcome = PrivacyNoticePage(driver).accept_and_continue()
    welcome.enter_mobile(INVALID_NUMBER)
    assert welcome.is_invalid_format_error_shown(ERROR_TIMEOUT), f"Expected '{welcome.INVALID_FORMAT_MESSAGE}'"
    assert not welcome.is_sign_up_enabled(), "SIGN UP! must stay disabled for an invalid number"
    assert not VerificationPage(driver).is_displayed(NEGATIVE_TIMEOUT), "Must not reach the verification screen"


@pytest.mark.zephyr
def test_already_registered_mobile_shows_login(driver, registration_otp):
    """Edge: a number that is already registered ends on the login page instead of creating an account."""
    welcome = PrivacyNoticePage(driver).accept_and_continue()
    verification = welcome.sign_up_with(REGISTERED_NUMBER)
    assert verification.is_displayed(VERIFICATION_TIMEOUT), "Verification Code screen should show after SIGN UP!"
    verification.enter_code(registration_otp)
    assert LoginPage(driver).is_displayed(LOGIN_TIMEOUT), "Login page should show for a registered number"


@pytest.mark.zephyr
def test_register_with_valid_mobile_and_otp(driver, registration_mobile, registration_otp, registration_password,
                                            profile_data):
    """Positive: a new (not yet registered) number gets a verification code and, with the OTP, reaches Complete Your Profile."""
    welcome = PrivacyNoticePage(driver).accept_and_continue()
    assert welcome.is_displayed(), "Welcome screen should offer SIGN UP!"
    verification = welcome.sign_up_with(registration_mobile)
    assert verification.is_displayed(VERIFICATION_TIMEOUT), "Verification Code screen should show after SIGN UP!"
    verification.enter_code(registration_otp)
    profile = ProfilePage(driver)
    assert profile.is_displayed(PROFILE_TIMEOUT), "Complete Your Profile should show once the OTP is accepted"
    profile.enter_name(FIRST_NAME, LAST_NAME).pick_birth_date(BIRTH_YEAR, BIRTH_DAY)
    assert profile.is_save_enabled(), "SAVE DETAILS should enable once the profile is filled"
    password_page = profile.save()
    assert password_page.is_displayed(PASSWORD_TIMEOUT), "Create Your Password should show after SAVE DETAILS"
    password_page.create_password(registration_password)
    assert password_page.is_submit_enabled(), "SUBMIT should enable for a password that meets every rule"
    customize = password_page.submit()
    assert customize.is_displayed(SUCCESS_TIMEOUT), "Customize Profile should show once the account is created"
    assert customize.is_almost_there_shown(), "The 'Almost there!' heading should show"
    customize.upload_avatar(AVATAR_DIR / profile_data["avatarFile"]).enter_nickname(profile_data["nickname"])
    assert customize.is_next_enabled(), "NEXT should enable once the nickname is entered"
    success = customize.next()
    nickname = profile_data["nickname"]
    assert success.is_greeting_shown(nickname, SUCCESS_TIMEOUT), f"Success page should greet 'All set, {nickname}!'"
    assert success.is_account_ready_message_shown(), "Success page should say the account is ready"
    assert success.is_continue_shown(), "Success page should offer CONTINUE"
