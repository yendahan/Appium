from __future__ import annotations

import time
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
SERVER_ERROR = (A11Y, "Internal server error")  # the app's error popup when the billers or a search fail
NEXT = (A11Y, "NEXT")
CONFIRM = (A11Y, "CONFIRM")
# A merchant (Asenso) account gets the "Customer E-Receipt" dialog over the receipt instead of the plain success screen.
RECEIPT = (XPATH, "//*[@content-desc='Payment Successful!' or @content-desc='Customer E-Receipt']")
E_RECEIPT = (A11Y, "Customer E-Receipt")
MAYBE_NEXT_TIME = (A11Y, "Maybe next time")  # closes the E-Receipt dialog and leaves the receipt
SUCCESS = (XPATH, "//*[contains(@content-desc,'Success')]")  # the receipt itself, once the dialog is closed

# The search icon (top right) and the first result row are not flagged clickable and expose no usable element,
# so they are tapped by position: 94% across / 8.5% down, and 45% across / 16.5% down.
SEARCH_ICON_X, SEARCH_ICON_Y = 0.942, 0.085
FIRST_RESULT_X, FIRST_RESULT_Y = 0.45, 0.165
# The magnifier inside the search field (once opened) submits the typed search: 89% across / 10.7% down.
SUBMIT_SEARCH_X, SUBMIT_SEARCH_Y = 0.892, 0.107

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
        deadline = time.monotonic() + BILLERS_TIMEOUT
        while not self.actions.is_visible(BILLERS_LOADED, 2):
            self.fail_on_server_error()
            if time.monotonic() > deadline:
                self.actions.wait_visible(BILLERS_LOADED, 1)  # raises with the usual "not visible" message
        return self

    def fail_on_server_error(self) -> None:
        """Fails the test when the app shows its 'Internal server error' popup (a backend failure, not a flaky wait)."""
        if self.actions.is_visible(SERVER_ERROR, 1):
            raise AssertionError("Pay Bills showed 'Internal server error'")

    def pay(self, biller: str, account_number: str, nickname: str, amount: str, tap_search: bool = False) -> "PayBillsPage":
        """Searches `biller` (`tap_search` taps the magnifier in the search field after typing), opens it, fills the biller form and taps NEXT."""
        a = self.actions
        a.tap_at(SEARCH_ICON_X, SEARCH_ICON_Y)
        a.type(SEARCH_FIELD, biller)
        if tap_search:
            a.tap_at(SUBMIT_SEARCH_X, SUBMIT_SEARCH_Y)
        if not a.is_visible(_biller_row(biller)):
            self.fail_on_server_error()
            a.wait_visible(_biller_row(biller), 1)  # raises with the usual "not visible" message
        if tap_search:
            a.tap_present(_biller_row(biller))  # a submitted search lists MERALCO first, so the first row is wrong
        else:
            a.tap_at(FIRST_RESULT_X, FIRST_RESULT_Y)
        a.wait_visible(ACCOUNT_NUMBER, FORM_TIMEOUT)  # the form shows a loading skeleton first
        if a.is_visible(NICKNAME, 3):  # the Asenso form has no nickname field
            a.type(NICKNAME, nickname)
        a.type(ACCOUNT_NUMBER, account_number)
        a.type(AMOUNT, amount)
        a.press_enter()  # Done key: the amount is only committed (and NEXT shown) when it loses focus; tapping the heading no longer blurs it
        a.tap(NEXT)
        return self

    def confirm(self) -> "PayBillsPage":
        self.actions.tap(CONFIRM)
        return self

    def is_review_displayed(self, timeout: Optional[float] = None) -> bool:
        return self.actions.is_visible(CONFIRM, timeout)

    def is_receipt_displayed(self, timeout: Optional[float] = None) -> bool:
        return self.actions.is_visible(RECEIPT, timeout)

    def is_e_receipt_displayed(self, timeout: Optional[float] = None) -> bool:
        return self.actions.is_visible(E_RECEIPT, timeout)

    def dismiss_e_receipt(self) -> "PayBillsPage":
        """Taps "Maybe next time" on the Customer E-Receipt dialog (merchant accounts) so the receipt behind it is visible."""
        self.actions.tap(MAYBE_NEXT_TIME)
        return self

    def is_payment_successful_displayed(self, timeout: Optional[float] = None) -> bool:
        return self.actions.is_visible(SUCCESS, timeout)
