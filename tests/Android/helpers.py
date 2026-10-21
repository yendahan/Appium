from __future__ import annotations

from framework.test_data_loader import TestDataLoader
from pages.biometric_setup_page import BiometricSetupPage
from pages.home_page import HomePage
from pages.privacy_notice_page import PrivacyNoticePage

ASENSO = "asensoCredentials"  # testdata node for the Asenso account tests
BASIC = "basicCredentials"  # testdata node for the Basic account tests
LOGIN_TIMEOUT = 60  # login + biometric screen can take 20s+ on a slow emulator


def log_in_to_home(driver, data: TestDataLoader, credentials_key: str = "credentials") -> None:
    if getattr(driver, "reused_session", False) and HomePage(driver).is_displayed(2):
        return  # --reuse-app: an earlier test of this account already logged in
    login = PrivacyNoticePage(driver).accept_and_continue().go_to_login()
    creds = data.node(credentials_key)
    login.login_as(creds["username"], creds["password"])
    biometric: BiometricSetupPage = login.expect_biometric_setup()
    assert biometric.is_displayed(LOGIN_TIMEOUT), "Biometric setup is offered after first login"
    assert biometric.skip().is_displayed(LOGIN_TIMEOUT), "Home screen should show after login"
