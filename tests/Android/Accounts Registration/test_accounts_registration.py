"""WARNING: registers (and upgrades) REG_COUNT real accounts on staging per run.

REG_MOBILE=9103221150 REG_PASSWORD=... REG_COUNT=3 pytest -m device "tests/Android/Accounts Registration"
REG_MOBILE is the first number to try, REG_COUNT how many accounts to create (default 1), REG_OTP overrides the default test OTP.
A number that is already registered ends on the login page: it is skipped and the next number (+1) is tried. Every account then
gets its own upgrade request, with the emulator camera for the ID photos, selfie and video."""
import logging
import os
import time
from pathlib import Path
from typing import List

import pytest

from framework.config_manager import ConfigManager
from framework.test_data_loader import TestDataLoader
from pages.login_page import LoginPage
from pages.privacy_notice_page import PrivacyNoticePage
from pages.profile_page import ProfilePage
from pages.upgrade_account_page import UpgradeAccountPage
from pages.verification_page import VerificationPage
from pages.welcome_page import WelcomePage
from tests.Android.helpers import log_in_to_home

LOG = logging.getLogger(__name__)

pytestmark = [pytest.mark.device, pytest.mark.risky]

AVATAR_DIR = Path(__file__).resolve().parents[3] / "testdata" / "avatar"
DEFAULT_OTP = "111111"
MAX_SKIPS = 20  # already-registered numbers skipped in a row before giving up
VERIFICATION_TIMEOUT = 60
OUTCOME_TIMEOUT = 60  # the OTP leads to Complete Your Profile, or to the login page for a registered number
PROFILE_TIMEOUT = 60
PASSWORD_TIMEOUT = 60
SUCCESS_TIMEOUT = 60  # account creation after SUBMIT takes ~15s
STEP_TIMEOUT = 60
SUBMITTED_TIMEOUT = 60
FIRST_NAME, LAST_NAME = "Test", "Automation"
BIRTH_YEAR, BIRTH_DAY = 1990, 15
DATA = TestDataLoader.for_current_env()
ACCOUNTS_FILE = Path(__file__).resolve().parents[3] / "artifacts" / "Accounts Registration" / "registered_accounts.txt"
UPGRADED_TITLE = "Registered and upgraded (upgrade submitted)"
REGISTERED_TITLE = "Registered, upgrade not submitted (not tried yet, or it failed)"

COUNT = max(int(os.environ.get("REG_COUNT", "1") or "1"), 1)
REGISTERED: List[str] = []  # the numbers created by this run, in order, for the upgrade tests


def record_account(mobile: str, upgraded: bool) -> None:
    """Keeps artifacts/Accounts Registration/registered_accounts.txt up to date: the number is listed under 'upgraded' once its upgrade is
    submitted, else under 'registered'. The file only ever holds numbers, never a password."""
    sections = {UPGRADED_TITLE: [], REGISTERED_TITLE: []}
    current = None
    if ACCOUNTS_FILE.is_file():
        for line in ACCOUNTS_FILE.read_text(encoding="utf-8").splitlines():
            if line.strip() in sections:
                current = line.strip()
            elif line.startswith("  ") and current and line.strip():
                sections[current].append(line.strip())
            elif line.strip() == "Notes":
                current = None
    for entries in sections.values():
        if mobile in entries:
            entries.remove(mobile)
    sections[UPGRADED_TITLE if upgraded else REGISTERED_TITLE].append(mobile)
    lines = ["Accounts Registration: numbers used (staging), kept up to date by test_accounts_registration.py", ""]
    for title, entries in sections.items():
        lines += [title] + [f"  {e}" for e in entries] + [""]
    lines += ["Notes", "  - The password is the REG_PASSWORD supplied for the run (never stored here)."]
    ACCOUNTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    ACCOUNTS_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")


def next_mobile(mobile: str) -> str:
    """The number after `mobile`, same length (9103221102 -> 9103221103)."""
    return str(int(mobile) + 1).zfill(len(mobile))


@pytest.fixture(scope="module")
def start_mobile() -> str:
    mobile = os.environ.get("REG_MOBILE", "").strip()
    if not mobile.isdigit():
        pytest.skip("set REG_MOBILE (the first number to try, e.g. 9100000001)")
    return mobile


@pytest.fixture(scope="module")
def password() -> str:
    value = os.environ.get("REG_PASSWORD", "")
    if not value:
        pytest.skip("set REG_PASSWORD (9+ chars, capital, number, symbol, no repeats or sequences)")
    return value


@pytest.fixture(scope="module")
def otp() -> str:
    return os.environ.get("REG_OTP", "").strip() or DEFAULT_OTP


def open_welcome(driver) -> WelcomePage:
    """The Welcome screen: straight away after an app restart, else through the Privacy Notice of a fresh app."""
    welcome = WelcomePage(driver)
    if welcome.is_displayed():
        return welcome
    return PrivacyNoticePage(driver).accept_and_continue()


def wait_for_outcome(driver) -> str:
    """'profile' when the OTP is accepted for a new number, 'login' when the number is already registered."""
    profile, login = ProfilePage(driver), LoginPage(driver)
    deadline = time.monotonic() + OUTCOME_TIMEOUT
    while time.monotonic() < deadline:
        if profile.is_displayed(1):
            return "profile"
        if login.is_displayed(1):
            return "login"
    return ""


@pytest.mark.parametrize("index", range(COUNT), ids=[f"account-{i + 1}" for i in range(COUNT)])
def test_register_account(driver, index, start_mobile, password, otp):
    """Positive: registers the next free number (skipping registered ones) and ends on the success page."""
    mobile = next_mobile(REGISTERED[-1]) if REGISTERED else start_mobile
    for _ in range(MAX_SKIPS + 1):
        welcome = open_welcome(driver)
        assert welcome.is_displayed(), "Welcome screen should offer SIGN UP!"
        verification = welcome.sign_up_with(mobile)
        assert verification.is_displayed(VERIFICATION_TIMEOUT), "Verification Code screen should show after SIGN UP!"
        verification.enter_code(otp)
        outcome = wait_for_outcome(driver)
        if outcome != "login":
            break
        LOG.info("%s is already registered, trying %s", mobile, next_mobile(mobile))
        mobile = next_mobile(mobile)
        WelcomePage(driver).actions.restart_app(ConfigManager.get_instance().get("app.package"))
    else:
        pytest.fail(f"{MAX_SKIPS} registered numbers in a row, last tried {mobile}")
    assert outcome == "profile", "Complete Your Profile should show once the OTP is accepted"

    profile = ProfilePage(driver)
    profile.enter_name(FIRST_NAME, LAST_NAME).pick_birth_date(BIRTH_YEAR, BIRTH_DAY)
    assert profile.is_save_enabled(), "SAVE DETAILS should enable once the profile is filled"
    password_page = profile.save()
    assert password_page.is_displayed(PASSWORD_TIMEOUT), "Create Your Password should show after SAVE DETAILS"
    password_page.create_password(password)
    assert password_page.is_submit_enabled(), "SUBMIT should enable for a password that meets every rule"
    customize = password_page.submit()
    assert customize.is_displayed(SUCCESS_TIMEOUT), "Customize Profile should show once the account is created"
    assert customize.is_almost_there_shown(), "The 'Almost there!' heading should show"
    profile_data = DATA.node("registration")
    customize.upload_avatar(AVATAR_DIR / profile_data["avatarFile"]).enter_nickname(profile_data["nickname"])
    assert customize.is_next_enabled(), "NEXT should enable once the nickname is entered"
    success = customize.next()
    nickname = profile_data["nickname"]
    assert success.is_greeting_shown(nickname, SUCCESS_TIMEOUT), f"Success page should greet 'All set, {nickname}!'"
    assert success.is_account_ready_message_shown(), "Success page should say the account is ready"
    assert success.is_continue_shown(), "Success page should offer CONTINUE"
    REGISTERED.append(mobile)
    record_account(mobile, upgraded=False)
    LOG.info("Registered account %d of %d: %s", index + 1, COUNT, mobile)


@pytest.mark.parametrize("index", range(COUNT), ids=[f"account-{i + 1}" for i in range(COUNT)])
def test_upgrade_account(driver, index, password):
    """Positive: the account registered by test_register_account[index] completes the Upgrade Account steps and submits."""
    if index >= len(REGISTERED):
        pytest.skip(f"account {index + 1} was not registered")
    info = DATA.node("upgradeAccount")
    log_in_to_home(driver, DATA, username=REGISTERED[index], password=password)
    upgrade = UpgradeAccountPage(driver).start()
    assert upgrade.is_profile_step_displayed(STEP_TIMEOUT), "Profile Information should show after UPGRADE NOW"
    upgrade.continue_from_profile()
    upgrade.fill_other_information(info["placeOfBirth"], info["nationality"], info["sourceOfFund"], info["natureOfWork"])
    upgrade.fill_address(info["province"], info["city"], info["street"])
    upgrade.choose_id(info["idType"], info["idNumber"])
    upgrade.capture_identity()
    assert upgrade.is_review_displayed(STEP_TIMEOUT), "Review Details should show after the identity verification"
    upgrade.submit()
    submitted = upgrade.is_submitted(SUBMITTED_TIMEOUT)
    upgrade.actions.screenshot(f"accountsRegistration-upgrade-{REGISTERED[index]}", "PASSED")
    assert submitted, "'Application Submitted!' should show after Submit"
    record_account(REGISTERED[index], upgraded=True)
