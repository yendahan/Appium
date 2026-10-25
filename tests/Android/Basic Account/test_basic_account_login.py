"""Needs an emulator with a screen lock and an enrolled fingerprint (adb shell locksettings set-pin 1234, then Settings > Security >
Fingerprint; see README): the fingerprint touch is sent through Appium and a physical phone cannot do that."""
import pytest

from framework.config_manager import ConfigManager
from framework.test_data_loader import TestDataLoader
from pages.biometric_prompt_page import BiometricPromptPage
from pages.home_page import HomePage
from pages.privacy_notice_page import PrivacyNoticePage
from tests.Android.helpers import BASIC

pytestmark = [pytest.mark.device, pytest.mark.risky]

SCREEN_TIMEOUT = 60
PROMPT_TIMEOUT = 30
DATA = TestDataLoader.for_current_env()


@pytest.mark.zephyr
def test_login_with_biometrics_after_enabling_it(driver):
    """Positive: biometrics enabled on the Biometric Setup screen lets the next app launch log in with the fingerprint."""
    page = PrivacyNoticePage(driver)
    if not page.actions.is_emulator():
        pytest.skip("the fingerprint touch can only be sent to an emulator")
    creds = DATA.node(BASIC)
    login = page.accept_and_continue().go_to_login()
    login.login_as(creds["username"], creds["password"])
    setup = login.expect_biometric_setup()
    assert setup.is_displayed(SCREEN_TIMEOUT), "Biometric Setup should be offered after the first login"
    prompt = setup.enable()
    assert prompt.is_displayed(PROMPT_TIMEOUT), "The fingerprint prompt should show after enabling biometrics"
    assert prompt.touch_sensor().is_displayed(SCREEN_TIMEOUT), "Home should show after the enrolled fingerprint is accepted"
    page.actions.restart_app(ConfigManager.get_instance().get("app.package"))
    prompt = BiometricPromptPage(driver)
    assert prompt.is_displayed(PROMPT_TIMEOUT), "The next launch should ask for the fingerprint instead of the password"
    home: HomePage = prompt.touch_sensor()
    assert home.is_displayed(SCREEN_TIMEOUT), "Home should show after logging in with the fingerprint"
    home.actions.screenshot("basicLoginWithBiometrics", "PASSED")
