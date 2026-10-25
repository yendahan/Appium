"""WARNING: submits a real account upgrade request on staging, once per number.

Run it right after the registration test, with the same number: REG_MOBILE=9100000001 REG_PASSWORD=... pytest -m device
"tests/Android/Basic Account/test_basic_account_registration.py" "tests/Android/Basic Account/test_basic_account_upgrade.py"
The upgrade wizard keeps its progress per account, so a number can be upgraded only once. The ID photos, selfie and video come
from the emulator camera."""
import os

import pytest

from framework.test_data_loader import TestDataLoader
from pages.upgrade_account_page import UpgradeAccountPage
from tests.Android.helpers import log_in_to_home

pytestmark = [pytest.mark.device, pytest.mark.risky]

STEP_TIMEOUT = 60
SUBMITTED_TIMEOUT = 60
DATA = TestDataLoader.for_current_env()


@pytest.fixture(scope="module")
def registered_credentials() -> dict:
    mobile = os.environ.get("REG_MOBILE", "").strip()
    password = os.environ.get("REG_PASSWORD", "")
    if not mobile or not password:
        pytest.skip("set REG_MOBILE and REG_PASSWORD (the number the registration test created) to run the upgrade test")
    return {"username": mobile, "password": password}


@pytest.mark.zephyr
def test_upgrade_account_after_registration(driver, registered_credentials):
    """Positive: a freshly registered Basic account completes the Upgrade Account steps and the request is submitted."""
    info = DATA.node("upgradeAccount")
    log_in_to_home(driver, DATA, **registered_credentials)
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
    upgrade.actions.screenshot("basicUpgradeAccount-submitted", "PASSED")
    assert submitted, "'Application Submitted!' should show after Submit"
