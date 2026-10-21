from __future__ import annotations

from typing import Optional

from appium.webdriver.common.appiumby import AppiumBy

from pages.base_page import BasePage

UIA = AppiumBy.ANDROID_UIAUTOMATOR
A11Y = AppiumBy.ACCESSIBILITY_ID

ACTIVITY_TAB = (AppiumBy.XPATH, "//android.widget.ImageView[starts-with(@content-desc,'Activity')]")  # bottom tab, desc "Activity\nTab 2 of 4"
WALLET_TAB = (A11Y, "Wallet\nTab 3 of 4")  # bottom tab
# the Wallet page first renders a placeholder; "See all" only works once the account has loaded
WALLET_LOADED = (UIA, 'new UiSelector().descriptionContains("Upgraded Account")')
SEE_ALL = (UIA, 'new UiSelector().descriptionStartsWith("See all")')  # beside the wallet's recent transactions
TRANSACTION_HISTORY = (UIA, 'new UiSelector().descriptionStartsWith("Transaction History")')
ONGOING_ACTIVITIES = (UIA, 'new UiSelector().descriptionStartsWith("Ongoing Activities")')
ROWS = (AppiumBy.XPATH, "//*[contains(@content-desc,'Success') or contains(@content-desc,'Pending') "
                        "or contains(@content-desc,'Failed')]")  # any transaction row
EMPTY = (AppiumBy.XPATH, "//*[contains(@content-desc,'No transactions')]")
# What a tab shows once loaded: the empty message, or any transaction row.
LOADED = (AppiumBy.XPATH, "//*[contains(@content-desc,'No transactions') or contains(@content-desc,'Success') "
                          "or contains(@content-desc,'Pending') or contains(@content-desc,'Failed')]")

LOAD_TIMEOUT = 30
EMPTY_RETRIES = 2  # "No transactions yet" can show before the list has loaded: return to the Wallet and open it again


class ActivityPage(BasePage):
    _reopen = None  # how this page was entered, repeated after a back press when a tab shows no transactions

    def open(self) -> "ActivityPage":
        self.actions.tap(ACTIVITY_TAB)
        self._reopen = self.open
        return self

    def open_from_wallet(self) -> "ActivityPage":
        a = self.actions
        a.tap(WALLET_TAB)
        a.wait_visible(WALLET_LOADED)
        a.tap(SEE_ALL)
        self._reopen = self.open_from_wallet
        return self

    def show_transaction_history(self) -> bool:
        """Opens (it is the default tab) Transaction History and waits for its list or empty message."""
        return self._show_tab(TRANSACTION_HISTORY)

    def show_ongoing_activities(self) -> bool:
        return self._show_tab(ONGOING_ACTIVITIES)

    def _show_tab(self, tab) -> bool:
        """Waits for the tab's list; on "No transactions yet" returns to the Wallet and reopens the page, then accepts the empty message."""
        a = self.actions
        a.tap(tab)
        for _ in range(EMPTY_RETRIES):
            if a.is_visible(ROWS, LOAD_TIMEOUT) or self._reopen is None:
                return True
            self._reopen()  # Back would leave the app; the Wallet tab is still on screen
            a.tap(tab)
        return a.is_visible(LOADED, LOAD_TIMEOUT)

    def is_displayed(self, timeout: Optional[float] = None) -> bool:
        a = self.actions
        return a.is_visible(TRANSACTION_HISTORY, timeout) and a.is_visible(ONGOING_ACTIVITIES, timeout)
