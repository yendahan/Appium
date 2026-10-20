from __future__ import annotations

from typing import Optional

from appium.webdriver.common.appiumby import AppiumBy

from pages.base_page import BasePage
from pages.biometric_setup_page import BiometricSetupPage

INVALID_CREDENTIALS_MESSAGE = "Incorrect username or password."

TITLE = (AppiumBy.ACCESSIBILITY_ID, "Log in to your account")
MOBILE = (AppiumBy.XPATH, "//android.widget.EditText[@hint='Mobile No.']")
PASSWORD = (AppiumBy.XPATH, "//android.widget.EditText[@hint='Password']")
LOG_IN_BUTTON = (AppiumBy.ACCESSIBILITY_ID, "LOG IN")
ERROR_MESSAGE = (AppiumBy.ACCESSIBILITY_ID, INVALID_CREDENTIALS_MESSAGE)
TRY_AGAIN = (AppiumBy.ACCESSIBILITY_ID, "TRY AGAIN")


class LoginPage(BasePage):
    INVALID_CREDENTIALS_MESSAGE = INVALID_CREDENTIALS_MESSAGE

    def is_displayed(self, timeout: Optional[float] = None) -> bool:
        return self.actions.is_visible(TITLE, timeout)

    def enter_mobile(self, mobile: str) -> "LoginPage":
        self.actions.type(MOBILE, mobile)
        return self

    def enter_password(self, password: str) -> "LoginPage":
        self.actions.type(PASSWORD, password)
        return self

    def is_submit_enabled(self) -> bool:
        return self.actions.is_enabled(LOG_IN_BUTTON)

    def submit(self) -> None:
        self.actions.tap(LOG_IN_BUTTON)

    def login_as(self, mobile: str, password: str) -> None:
        self.enter_mobile(mobile).enter_password(password).submit()

    def mobile_field_text(self) -> str:
        return self.actions.text(MOBILE)

    def is_invalid_credentials_error_shown(self, timeout: Optional[float] = None) -> bool:
        return self.actions.is_visible(ERROR_MESSAGE, timeout)

    def dismiss_error(self) -> "LoginPage":
        self.actions.tap(TRY_AGAIN)
        return self

    def expect_biometric_setup(self) -> BiometricSetupPage:
        return BiometricSetupPage(self.driver)
