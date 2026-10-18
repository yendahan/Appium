from __future__ import annotations

from framework.test_data_loader import TestDataLoader
from pages.biometric_setup_page import BiometricSetupPage
from pages.privacy_notice_page import PrivacyNoticePage

LOGIN_TIMEOUT = 20


def log_in_to_home(driver, data: TestDataLoader) -> None:
    login = PrivacyNoticePage(driver).accept_and_continue().go_to_login()
    creds = data.node("credentials")
    login.login_as(creds["username"], creds["password"])
    biometric: BiometricSetupPage = login.expect_biometric_setup()
    assert biometric.is_displayed(LOGIN_TIMEOUT), "Biometric setup is offered after first login"
    assert biometric.skip().is_displayed(LOGIN_TIMEOUT), "Home screen should show after login"
