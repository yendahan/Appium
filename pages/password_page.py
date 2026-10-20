from __future__ import annotations

from typing import Optional

from appium.webdriver.common.appiumby import AppiumBy

from pages.base_page import BasePage
from pages.customize_profile_page import CustomizeProfilePage

TITLE = (AppiumBy.ACCESSIBILITY_ID, "Create Your Password")
PASSWORD = (AppiumBy.XPATH, "//android.widget.EditText[@hint='Create your password']")
CONFIRM = (AppiumBy.XPATH, "//android.widget.EditText[@hint='Confirm your password']")
SUBMIT = (AppiumBy.ACCESSIBILITY_ID, "SUBMIT")


class PasswordPage(BasePage):
    def is_displayed(self, timeout: Optional[float] = None) -> bool:
        return self.actions.is_visible(TITLE, timeout)

    def create_password(self, password: str) -> "PasswordPage":
        self.actions.type(PASSWORD, password)
        self.actions.type(CONFIRM, password)
        return self

    def is_submit_enabled(self) -> bool:
        return self.actions.is_enabled(SUBMIT)

    def submit(self) -> CustomizeProfilePage:
        self.actions.tap(SUBMIT)
        return CustomizeProfilePage(self.driver)
