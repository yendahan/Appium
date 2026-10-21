from __future__ import annotations

from typing import Optional

from appium.webdriver.common.appiumby import AppiumBy

from pages.base_page import BasePage

SERVICES = (AppiumBy.ACCESSIBILITY_ID, "Services")
HOME_TAB = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().descriptionStartsWith("Home")')  # bottom tab, desc "Home\nTab 1 of 4"
YES_GO_BACK = (AppiumBy.ACCESSIBILITY_ID, "YES, GO BACK")  # the "Go back?" dialog some forms ask first

BACK_PRESSES = 5
HOME_TIMEOUT = 10


class HomePage(BasePage):
    def is_displayed(self, timeout: Optional[float] = None) -> bool:
        return self.actions.is_visible(SERVICES, timeout)

    def return_to_home(self) -> bool:
        """Backs out of whatever screen is open until the Home tab shows, then taps it; False if Home is not reached."""
        a = self.actions
        for _ in range(BACK_PRESSES):
            if a.is_visible(HOME_TAB, 2):
                a.tap(HOME_TAB)
                return self.is_displayed(HOME_TIMEOUT)
            if a.is_visible(YES_GO_BACK, 1):
                a.tap(YES_GO_BACK)
            else:
                a.press_back()
        return False
