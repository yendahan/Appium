from __future__ import annotations

from typing import Optional

from appium.webdriver.common.appiumby import AppiumBy

from pages.base_page import BasePage
from pages.login_page import LoginPage
from pages.verification_page import VerificationPage

MOBILE = (AppiumBy.XPATH, "//android.widget.EditText[@hint='Mobile Number']")
INVALID_FORMAT_MESSAGE = "Invalid mobile number format. Ex: (+63) 9191234567"
INVALID_FORMAT = (AppiumBy.ACCESSIBILITY_ID, INVALID_FORMAT_MESSAGE)
SIGN_UP_BUTTON = (AppiumBy.ACCESSIBILITY_ID, "SIGN UP!")
LOG_IN_LINK = (AppiumBy.ACCESSIBILITY_ID, "Log in")


class WelcomePage(BasePage):
    INVALID_FORMAT_MESSAGE = INVALID_FORMAT_MESSAGE

    def is_displayed(self) -> bool:
        return self.actions.is_visible(SIGN_UP_BUTTON)

    def enter_mobile(self, mobile: str) -> "WelcomePage":
        self.actions.type(MOBILE, mobile)
        return self

    def is_sign_up_enabled(self) -> bool:
        return self.actions.is_enabled(SIGN_UP_BUTTON)

    def is_invalid_format_error_shown(self, timeout: Optional[float] = None) -> bool:
        return self.actions.is_visible(INVALID_FORMAT, timeout)

    def sign_up_with(self, mobile: str) -> VerificationPage:
        self.enter_mobile(mobile)
        self.actions.tap(SIGN_UP_BUTTON)
        return VerificationPage(self.driver)

    def go_to_login(self) -> LoginPage:
        self.actions.tap(LOG_IN_LINK)
        return LoginPage(self.driver)
