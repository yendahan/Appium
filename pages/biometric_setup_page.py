from __future__ import annotations

from typing import Optional

from appium.webdriver.common.appiumby import AppiumBy

from pages.base_page import BasePage
from pages.biometric_prompt_page import BiometricPromptPage
from pages.home_page import HomePage

TITLE = (AppiumBy.ACCESSIBILITY_ID, "Biometric Setup")
SKIP = (AppiumBy.ACCESSIBILITY_ID, "Maybe next time")
ENABLE = (AppiumBy.ACCESSIBILITY_ID, "GAME!")  # the button's label on staging
CONFIRM_TITLE = (AppiumBy.ACCESSIBILITY_ID, "Enable Biometrics Authentication")
CONFIRM_YES = (AppiumBy.ACCESSIBILITY_ID, "YES")


class BiometricSetupPage(BasePage):
    def is_displayed(self, timeout: Optional[float] = None) -> bool:
        return self.actions.is_visible(TITLE, timeout)

    def enable(self) -> "BiometricPromptPage":
        """GAME! then YES on the "Enable Biometrics Authentication" dialog opens the fingerprint prompt."""
        a = self.actions
        a.tap(ENABLE)
        a.wait_visible(CONFIRM_TITLE)
        a.tap(CONFIRM_YES)
        return BiometricPromptPage(self.driver)

    def skip(self) -> HomePage:
        self.actions.tap(SKIP)
        return HomePage(self.driver)
