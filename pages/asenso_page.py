from __future__ import annotations

from typing import List, Optional

from appium.webdriver.common.appiumby import AppiumBy

from pages.base_page import BasePage

A11Y = AppiumBy.ACCESSIBILITY_ID
XPATH = AppiumBy.XPATH

PAY_BILLS_TILE = (A11Y, "Pay Bills")  # a Services tile: it shows once the skeleton tiles have loaded
SEE_ALL = (XPATH, "(//android.widget.Button[@content-desc='See All'])[2]")  # the Services one; the first is the announcements'
ASENSO_TILE = (A11Y, "Asenso")  # in the Business group, below the fold of All Services
ASENSO_HOME = (A11Y, "Asenso Wallet")
MY_TRANSACTIONS = (A11Y, "my transactions")
TRANSACTION_HISTORY = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().descriptionStartsWith("Transaction History")')
ACTIVITY_TITLE = (A11Y, "Activity")

BACK = (A11Y, "Back")
ADD_MONEY = (A11Y, "Add Money")
WITHDRAW_MONEY = (A11Y, "Withdraw Money")
PAY_BILLS = (A11Y, "Pay Bills")
FROM_WALLET_TAB = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().descriptionStartsWith("From My Bayad Wallet")')
AMOUNT = (XPATH, "//android.widget.EditText[@hint='Amount']")
ENTER_AMOUNT = (A11Y, "Enter Amount")  # heading: tapping it drops focus, which commits the amount and enables NEXT
NEXT = (A11Y, "NEXT")
CONFIRMATION = (A11Y, "Transaction Confirmation")
CONFIRM = (A11Y, "CONFIRM")
# The receipt screen was not captured when these were written (no real transfer during discovery): matches any
# "...Successful..." / "...Success..." text on the screen.
SUCCESS = (XPATH, "//*[contains(@content-desc,'Success')]")

AVATAR_X, AVATAR_Y = 0.433, 0.12  # the round avatar left of the name: not exposed as an element
ADD_MONEY_ROW_X, ADD_MONEY_ROW_Y = 0.5, 0.407  # "From My Bayad Wallet" row under the method tabs
WITHDRAW_ROW_X, WITHDRAW_ROW_Y = 0.5, 0.47  # "To My Bayad Wallet" row

ACCOUNT_MANAGEMENT = (A11Y, "Account Management")
GENERAL_SETTINGS = (A11Y, "General Settings")
# Account Management links: an element that only exists once the screen's content has loaded (its heading shows first).
LINK_CONTENT = {
    "InstaPay Settings": (XPATH, "//*[contains(@content-desc,'Balance: Php')]"),  # the wallet options, after a spinner
    "Input Distributor Code": (XPATH, "//android.widget.EditText[@hint='Distributor Code']"),
    "Upload Business Permit": (XPATH, "//android.widget.EditText[@hint='Business Permit Number']"),
    "Terms and Conditions": (XPATH, "//*[contains(@text,'Welcome to Bayad by CIS Bayad Center')]"),  # web page body
    "Data Privacy": (XPATH, "//*[@text='BAYAD AND DATA PRIVACY']"),  # web page body
    "User Manual": (XPATH, "//android.widget.ImageView"),  # the manual's page image, after a blank web view
}
YES_GO_BACK = (A11Y, "YES, GO BACK")  # the "Go back?" dialog that forms (e.g. Input Distributor Code) ask first

HOME_TIMEOUT = 60  # service tiles and the Asenso screen load slowly
LOAD_TIMEOUT = 30


class AsensoPage(BasePage):
    def open(self) -> "AsensoPage":
        """Home > Services > See All > scroll to Asenso (Business group) > Asenso."""
        a = self.actions
        a.wait_visible(PAY_BILLS_TILE, HOME_TIMEOUT)
        a.tap(SEE_ALL)
        a.wait_visible(ADD_MONEY, LOAD_TIMEOUT)
        a.scroll_to_description("Asenso")
        a.tap(ASENSO_TILE)
        a.wait_visible(ASENSO_HOME, HOME_TIMEOUT)
        return self

    def is_displayed(self, timeout: Optional[float] = None) -> bool:
        return self.actions.is_visible(ASENSO_HOME, timeout)

    # --- add / withdraw money ----------------------------------------------------------------------------------
    def add_money_from_wallet(self, amount: str) -> "AsensoPage":
        """Add Money > From My Bayad Wallet > amount > NEXT (stops on the Transaction Confirmation screen)."""
        a = self.actions
        a.tap(ADD_MONEY)
        a.wait_visible(FROM_WALLET_TAB, LOAD_TIMEOUT)
        a.tap_at(ADD_MONEY_ROW_X, ADD_MONEY_ROW_Y)
        return self._enter_amount(amount)

    def withdraw_to_wallet(self, amount: str) -> "AsensoPage":
        """Withdraw Money > To My Bayad Wallet > amount > NEXT (stops on the Transaction Confirmation screen)."""
        a = self.actions
        a.tap(WITHDRAW_MONEY)
        a.wait_visible((A11Y, "Select Withdraw Money Method"), LOAD_TIMEOUT)
        a.tap_at(WITHDRAW_ROW_X, WITHDRAW_ROW_Y)
        return self._enter_amount(amount)

    def _enter_amount(self, amount: str) -> "AsensoPage":
        a = self.actions
        a.wait_visible(ENTER_AMOUNT, HOME_TIMEOUT)  # the form shows a spinner first
        a.type(AMOUNT, amount)
        a.tap(ENTER_AMOUNT)
        a.tap(NEXT)
        return self

    def is_confirmation_displayed(self, timeout: Optional[float] = None) -> bool:
        return self.actions.is_visible(CONFIRMATION, timeout)

    def confirm(self) -> "AsensoPage":
        self.actions.tap(CONFIRM)
        return self

    def is_success_displayed(self, timeout: Optional[float] = None) -> bool:
        return self.actions.is_visible(SUCCESS, timeout)

    # --- pay bills ---------------------------------------------------------------------------------------------
    def open_pay_bills(self) -> None:
        """Opens Pay Bills from the Asenso screen; the caller continues with PayBillsPage (same screens as Bayad's)."""
        self.actions.tap(PAY_BILLS)

    # --- my transactions ---------------------------------------------------------------------------------------
    def open_my_transactions(self) -> "AsensoPage":
        self.actions.tap(MY_TRANSACTIONS)
        return self

    def is_transaction_history_displayed(self, timeout: Optional[float] = None) -> bool:
        a = self.actions
        return a.is_visible(ACTIVITY_TITLE, timeout) and a.is_visible(TRANSACTION_HISTORY, timeout)

    def transaction_rows(self) -> List[str]:
        """The accessibility text of the history rows (e.g. 'Add Money\\n11:00 AM\\n100.00\\n...\\nSuccess')."""
        rows = self.driver.find_elements(XPATH, "//*[contains(@content-desc,'Success') or contains(@content-desc,'Pending') "
                                                "or contains(@content-desc,'Failed')]")
        return [r.get_attribute("content-desc") for r in rows]

    # --- account management ------------------------------------------------------------------------------------
    def open_account_management(self) -> "AsensoPage":
        """Taps the avatar left of the name (not exposed as an element, so tapped by position)."""
        self.actions.tap_at(AVATAR_X, AVATAR_Y)
        return self

    def is_account_management_displayed(self, timeout: Optional[float] = None) -> bool:
        return self.actions.is_visible(GENERAL_SETTINGS, timeout)

    def is_link_displayed(self, link: str, timeout: Optional[float] = None) -> bool:
        return self.actions.is_visible((A11Y, link), timeout)

    def open_link(self, link: str) -> None:
        self.actions.tap((A11Y, link))

    def is_heading_displayed(self, heading: str, timeout: Optional[float] = None) -> bool:
        return self.actions.is_visible((A11Y, heading), timeout)

    def is_link_content_displayed(self, link: str, timeout: Optional[float] = None) -> bool:
        """The link's screen has finished loading (its heading shows before its content)."""
        return self.actions.is_visible(LINK_CONTENT[link], timeout)

    def back_to_account_management(self) -> bool:
        """Back from a link's screen; more than one Back is needed when the first only closes the keyboard."""
        a = self.actions
        for _ in range(3):
            if a.is_visible(BACK, 3):
                a.tap(BACK)
            else:
                a.press_back()  # web pages (terms, privacy, manual) have no Back button of their own
            if a.is_visible(YES_GO_BACK, 5):  # the confirmation dialog can take a few seconds to show
                a.tap(YES_GO_BACK)
            if a.is_visible(GENERAL_SETTINGS, 5):
                return True
        return False
