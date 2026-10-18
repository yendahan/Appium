from __future__ import annotations

from appium.webdriver.common.appiumby import AppiumBy

from pages.base_page import BasePage
from pages.welcome_page import WelcomePage

TITLE = (AppiumBy.ACCESSIBILITY_ID, "Privacy Notice")
AGREE = (AppiumBy.ACCESSIBILITY_ID, "AGREE & CONTINUE")


class PrivacyNoticePage(BasePage):
    def is_displayed(self) -> bool:
        return self.actions.is_visible(TITLE)

    def accept_and_continue(self) -> WelcomePage:
        self.actions.tap(AGREE)
        return WelcomePage(self.driver)
