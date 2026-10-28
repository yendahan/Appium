from __future__ import annotations

from typing import Optional

from appium.webdriver.common.appiumby import AppiumBy

from pages.base_page import BasePage

A11Y = AppiumBy.ACCESSIBILITY_ID

ADD_MONEY = (A11Y, "Add Money")  # a Services tile: it shows once the skeleton tiles have loaded
OVER_THE_COUNTER = (A11Y, "Over the Counter")
AMOUNT = (AppiumBy.XPATH, "//android.widget.EditText[@hint='Enter Amount']")
AMOUNT_HEADING = (A11Y, "Enter or Select Amount (Php)")  # tapping it drops focus, which commits the amount and enables NEXT
NEXT = (A11Y, "NEXT")
CONFIRMATION = (A11Y, "Payment Confirmation")
CONFIRM = (A11Y, "CONFIRM")
SUCCESS = (AppiumBy.XPATH, "//*[contains(@content-desc,'Success')]")  # the receipt after CONFIRM
MINIMUM_ERROR = (A11Y, "The minimum cash-in amount is 300.")

# The partner rows ("Bayad Center", "Pera Hub") are not tapped reliably by element: the first row is tapped by position.
BAYAD_CENTER_X, BAYAD_CENTER_Y = 0.5, 0.505

HOME_TIMEOUT = 60  # the service tiles load after the home screen
LOAD_TIMEOUT = 30


class AddMoneyPage(BasePage):
    def open(self) -> "AddMoneyPage":
        """Home > Add Money (Services tile) > Over the Counter > Bayad Center, ready for the amount."""
        a = self.actions
        a.wait_visible(ADD_MONEY, HOME_TIMEOUT)
        a.tap(ADD_MONEY)
        a.wait_visible(OVER_THE_COUNTER, LOAD_TIMEOUT)
        a.tap(OVER_THE_COUNTER)
        a.wait_visible((AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().descriptionStartsWith("Bayad Center")'), LOAD_TIMEOUT)
        a.tap_at(BAYAD_CENTER_X, BAYAD_CENTER_Y)
        a.wait_visible(AMOUNT_HEADING, LOAD_TIMEOUT)
        return self

    def enter_amount(self, amount: str) -> "AddMoneyPage":
        a = self.actions
        a.type(AMOUNT, amount)
        a.tap(AMOUNT_HEADING)
        return self

    def next(self) -> "AddMoneyPage":
        self.actions.tap(NEXT)
        return self

    def next_is_enabled(self) -> bool:
        return self.actions.is_enabled(NEXT)

    def confirm(self) -> "AddMoneyPage":
        self.actions.tap(CONFIRM)
        return self

    def is_success_displayed(self, timeout: Optional[float] = None) -> bool:
        return self.actions.is_visible(SUCCESS, timeout)

    def is_confirmation_displayed(self, timeout: Optional[float] = None) -> bool:
        return self.actions.is_visible(CONFIRMATION, timeout)

    def is_minimum_error_displayed(self, timeout: Optional[float] = None) -> bool:
        return self.actions.is_visible(MINIMUM_ERROR, timeout)
