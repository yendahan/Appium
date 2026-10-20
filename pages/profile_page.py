from __future__ import annotations

from typing import Optional

from appium.webdriver.common.appiumby import AppiumBy

from pages.base_page import BasePage
from pages.password_page import PasswordPage

TITLE = (AppiumBy.ACCESSIBILITY_ID, "Complete Your Profile")
FIRST_NAME = (AppiumBy.XPATH, "//android.widget.EditText[@hint='First Name']")
LAST_NAME = (AppiumBy.XPATH, "//android.widget.EditText[@hint='Last Name']")
DATE_OF_BIRTH = (AppiumBy.XPATH, "//*[@hint='Date of Birth']")
SELECT_YEAR = (AppiumBy.XPATH, "//android.widget.Button[starts-with(@content-desc,'Select year')]")
DATE_OK = (AppiumBy.ACCESSIBILITY_ID, "OK")
SAVE_DETAILS = (AppiumBy.ACCESSIBILITY_ID, "SAVE DETAILS")


def _day(day: int) -> tuple:
    return AppiumBy.XPATH, f"//android.widget.Button[starts-with(@content-desc,'{day},')]"


class ProfilePage(BasePage):
    def is_displayed(self, timeout: Optional[float] = None) -> bool:
        return self.actions.is_visible(TITLE, timeout)

    def enter_name(self, first: str, last: str) -> "ProfilePage":
        self.actions.type(FIRST_NAME, first)
        self.actions.type(LAST_NAME, last)
        self.actions.tap(TITLE)  # drop focus so the keyboard closes (hide_keyboard() acts as Back and leaves the screen)
        return self

    def pick_birth_date(self, year: int, day: int) -> "ProfilePage":
        """Opens the date picker and picks `day` of the month it opens on, in `year`."""
        self.actions.tap_present(DATE_OF_BIRTH)
        self.actions.tap(SELECT_YEAR)
        if not self.actions.scroll_to_description(str(year)):
            raise AssertionError(f"Year {year} not found in the date picker")
        self.actions.tap((AppiumBy.ACCESSIBILITY_ID, str(year)))
        self.actions.tap(_day(day))
        self.actions.tap(DATE_OK)
        return self

    def is_save_enabled(self) -> bool:
        return self.actions.is_enabled(SAVE_DETAILS)

    def save(self) -> PasswordPage:
        self.actions.tap(SAVE_DETAILS)
        return PasswordPage(self.driver)
