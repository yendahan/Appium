from __future__ import annotations

from typing import Optional

from appium.webdriver.common.appiumby import AppiumBy

from pages.base_page import BasePage

A11Y = AppiumBy.ACCESSIBILITY_ID
XPATH = AppiumBy.XPATH

SERVICES = (A11Y, "Services")
PAY_BILLS = (A11Y, "Pay Bills")
# The category grid only renders once the billers have loaded; WATER is one of its tiles.
BILLERS_LOADED = (A11Y, "WATER")
SEARCH_FIELD = (XPATH, "//android.widget.EditText[@hint='Search Billers']")
NICKNAME = (XPATH, "//android.widget.EditText[@hint='Preferred Biller Nickname']")
ACCOUNT_NUMBER = (XPATH, "//android.widget.EditText[@hint='Account Number']")
AMOUNT = (XPATH, "//android.widget.EditText[@hint='Amount']")
FORM_HEADING = (A11Y, "Enter Biller Information")
NEXT = (A11Y, "NEXT")
CONFIRM = (A11Y, "CONFIRM")
RECEIPT = (A11Y, "Payment Successful!")

# The search icon (top right) and the first result row are not flagged clickable and expose no usable element,
# so they are tapped by position: 94% across / 8.5% down, and 45% across / 16.5% down.
SEARCH_ICON_X, SEARCH_ICON_Y = 0.942, 0.085
FIRST_RESULT_X, FIRST_RESULT_Y = 0.45, 0.165

BILLERS_TIMEOUT = 60
FORM_TIMEOUT = 60


def _biller_row(biller: str):
    return XPATH, f"//*[starts-with(@content-desc,'{biller.upper()}')]"


class PayBillsPage(BasePage):
    def open(self) -> "PayBillsPage":
        """Services > Pay Bills, then waits for the billers to load (the search button does nothing before that)."""
        self.actions.tap(SERVICES)
        self.actions.wait_visible(PAY_BILLS, FORM_TIMEOUT)  # the service tiles load after the home screen
        self.actions.tap(PAY_BILLS)
        return self.wait_for_billers()

    def wait_for_billers(self) -> "PayBillsPage":
        """Waits for the biller categories (also the entry point when Pay Bills was opened from another screen)."""
        self.actions.wait_visible(BILLERS_LOADED, BILLERS_TIMEOUT)
        return self

    def pay(self, biller: str, account_number: str, nickname: str, amount: str) -> "PayBillsPage":
        """Searches `biller`, opens it, fills the biller form and taps NEXT."""
        a = self.actions
        a.tap_at(SEARCH_ICON_X, SEARCH_ICON_Y)
        a.type(SEARCH_FIELD, biller)
        a.wait_visible(_biller_row(biller))
        a.tap_at(FIRST_RESULT_X, FIRST_RESULT_Y)
        a.wait_visible(NICKNAME, FORM_TIMEOUT)  # the form shows a loading skeleton first
        a.type(NICKNAME, nickname)
        a.type(ACCOUNT_NUMBER, account_number)
        a.type(AMOUNT, amount)
        a.tap(FORM_HEADING)  # blur: the amount is only committed (and NEXT enabled) when it loses focus
        a.tap(NEXT)
        return self

    def confirm(self) -> "PayBillsPage":
        self.actions.tap(CONFIRM)
        return self

    def is_review_displayed(self, timeout: Optional[float] = None) -> bool:
        return self.actions.is_visible(CONFIRM, timeout)

    def is_receipt_displayed(self, timeout: Optional[float] = None) -> bool:
        return self.actions.is_visible(RECEIPT, timeout)
