from __future__ import annotations

from typing import Optional

from appium.webdriver.common.appiumby import AppiumBy

from pages.base_page import BasePage
from pages.home_page import HomePage

PROMPT = (AppiumBy.ACCESSIBILITY_ID, "Fingerprint sensor")  # the system fingerprint dialog


class BiometricPromptPage(BasePage):
    def is_displayed(self, timeout: Optional[float] = None) -> bool:
        return self.actions.is_visible(PROMPT, timeout)

    def touch_sensor(self) -> HomePage:
        """Touches the enrolled fingerprint (emulator only); the app then opens Home."""
        self.actions.touch_fingerprint()
        return HomePage(self.driver)
