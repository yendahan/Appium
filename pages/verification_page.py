from __future__ import annotations

from typing import Optional

from appium.webdriver.common.appiumby import AppiumBy

from pages.base_page import BasePage

TITLE = (AppiumBy.ACCESSIBILITY_ID, "Verification Code")
# The 6 code boxes are a custom widget: typing into its EditText shows nothing, so tap the first box
# (about 20% across, 32% down) to open the keyboard and press digit keys instead.
CODE_BOX_X, CODE_BOX_Y = 0.20, 0.32


class VerificationPage(BasePage):
    def is_displayed(self, timeout: Optional[float] = None) -> bool:
        return self.actions.is_visible(TITLE, timeout)

    def enter_code(self, code: str) -> "VerificationPage":
        self.actions.tap_at(CODE_BOX_X, CODE_BOX_Y)
        self.actions.press_digits(code)
        return self
