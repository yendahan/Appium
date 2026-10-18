from __future__ import annotations

from typing import Optional

from appium.webdriver.common.appiumby import AppiumBy

from pages.base_page import BasePage

SERVICES = (AppiumBy.ACCESSIBILITY_ID, "Services")


class HomePage(BasePage):
    def is_displayed(self, timeout: Optional[float] = None) -> bool:
        return self.actions.is_visible(SERVICES, timeout)
