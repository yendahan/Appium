from __future__ import annotations

from typing import Optional

from appium.webdriver.common.appiumby import AppiumBy

from pages.base_page import BasePage
from pages.home_page import HomePage

TITLE = (AppiumBy.ACCESSIBILITY_ID, "Biometric Setup")
SKIP = (AppiumBy.ACCESSIBILITY_ID, "Maybe next time")


class BiometricSetupPage(BasePage):
    def is_displayed(self, timeout: Optional[float] = None) -> bool:
        return self.actions.is_visible(TITLE, timeout)

    def skip(self) -> HomePage:
        self.actions.tap(SKIP)
        return HomePage(self.driver)
