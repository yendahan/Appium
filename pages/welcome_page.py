from __future__ import annotations

from appium.webdriver.common.appiumby import AppiumBy

from pages.base_page import BasePage
from pages.login_page import LoginPage

SIGN_UP_BUTTON = (AppiumBy.ACCESSIBILITY_ID, "SIGN UP!")
LOG_IN_LINK = (AppiumBy.ACCESSIBILITY_ID, "Log in")


class WelcomePage(BasePage):
    def is_displayed(self) -> bool:
        return self.actions.is_visible(SIGN_UP_BUTTON)

    def go_to_login(self) -> LoginPage:
        self.actions.tap(LOG_IN_LINK)
        return LoginPage(self.driver)
