from __future__ import annotations

from typing import Optional

from appium.webdriver.common.appiumby import AppiumBy

from pages.base_page import BasePage

UIA = AppiumBy.ANDROID_UIAUTOMATOR

ACTIVITY_TAB = (AppiumBy.XPATH, "//android.widget.ImageView[starts-with(@content-desc,'Activity')]")  # bottom tab, desc "Activity\nTab 2 of 4"
TRANSACTION_HISTORY = (UIA, 'new UiSelector().descriptionStartsWith("Transaction History")')
ONGOING_ACTIVITIES = (UIA, 'new UiSelector().descriptionStartsWith("Ongoing Activities")')
# What a tab shows once loaded: the empty message, or any transaction row.
LOADED = (AppiumBy.XPATH, "//*[contains(@content-desc,'No transactions') or contains(@content-desc,'Success') "
                          "or contains(@content-desc,'Pending') or contains(@content-desc,'Failed')]")

LOAD_TIMEOUT = 30


class ActivityPage(BasePage):
    def open(self) -> "ActivityPage":
        self.actions.tap(ACTIVITY_TAB)
        return self

    def show_transaction_history(self) -> bool:
        """Opens (it is the default tab) Transaction History and waits for its list or empty message."""
        a = self.actions
        a.tap(TRANSACTION_HISTORY)
        return a.is_visible(LOADED, LOAD_TIMEOUT)

    def show_ongoing_activities(self) -> bool:
        a = self.actions
        a.tap(ONGOING_ACTIVITIES)
        return a.is_visible(LOADED, LOAD_TIMEOUT)

    def is_displayed(self, timeout: Optional[float] = None) -> bool:
        a = self.actions
        return a.is_visible(TRANSACTION_HISTORY, timeout) and a.is_visible(ONGOING_ACTIVITIES, timeout)
