from __future__ import annotations

from typing import Optional

from appium.webdriver.common.appiumby import AppiumBy

from pages.base_page import BasePage

MESSAGE = (AppiumBy.ACCESSIBILITY_ID, "Your account is now ready. Click CONTINUE to level up your Bayad Experience!")
CONTINUE = (AppiumBy.ACCESSIBILITY_ID, "CONTINUE")


class RegistrationSuccessPage(BasePage):
    def is_greeting_shown(self, nickname: str, timeout: Optional[float] = None) -> bool:
        return self.actions.is_visible((AppiumBy.ACCESSIBILITY_ID, f"All set, {nickname}!"), timeout)

    def is_account_ready_message_shown(self, timeout: Optional[float] = None) -> bool:
        return self.actions.is_visible(MESSAGE, timeout)

    def is_continue_shown(self, timeout: Optional[float] = None) -> bool:
        return self.actions.is_visible(CONTINUE, timeout)
