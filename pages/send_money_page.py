from __future__ import annotations

import base64
from pathlib import Path
from typing import Optional

from appium.webdriver.common.appiumby import AppiumBy
from selenium.common.exceptions import WebDriverException

from framework.exceptions import FrameworkException
from pages.base_page import BasePage

A11Y = AppiumBy.ACCESSIBILITY_ID
XPATH = AppiumBy.XPATH
UIA = AppiumBy.ANDROID_UIAUTOMATOR

SERVICES = (A11Y, "Services")
SEND_MONEY = (A11Y, "Send Money")
VIA_QR = (A11Y, "Via QR")
TO_BAYAD_WALLET = (A11Y, "To Bayad Wallet")
TO_OTHER_BANKS = (A11Y, "To Other Banks and E-Wallets")
UPLOAD_QR = (A11Y, "Upload QR from Gallery")
SEND_TO = (XPATH, "//android.widget.EditText[@hint='Send money to']")
AMOUNT = (XPATH, "//android.widget.EditText[@hint='Enter cash amount']")
ACCOUNT_NO = (XPATH, "//android.widget.EditText[@hint='Account No.']")
BANK_AMOUNT = (XPATH, "//android.widget.EditText[@hint='Amount']")
ACCOUNT_NAME = (XPATH, "//android.widget.EditText[@hint='Account Name']")
NEWEST_PHOTO = (UIA, 'new UiSelector().descriptionStartsWith("Photo taken").instance(0)')
PICKER_DONE = (XPATH, "//*[@text='Done' or @content-desc='Done']")
AMOUNT_HEADING = (A11Y, "Enter or Select Amount (Php)")
SEARCH_ICON = (XPATH, "(//android.widget.Button)[2]")  # unlabeled, top right
BANK_SEARCH = (AppiumBy.CLASS_NAME, "android.widget.EditText")
SUCCESS = (XPATH, "//*[contains(@content-desc,'Successfully Sent')]")
CONFIRM = (A11Y, "CONFIRM")
NEXT = (A11Y, "NEXT")
REVIEW = (XPATH, "//*[@content-desc='Send Money Confirmation' or @content-desc='Payment Confirmation']")

SEARCH_ATTEMPTS = 2
BANK_LIST_ATTEMPTS = 3
GALLERY_DIR = "/sdcard/Pictures/"


class SendMoneyPage(BasePage):
    def open(self) -> "SendMoneyPage":
        self.actions.tap(SERVICES)
        self.actions.tap(SEND_MONEY)
        return self

    def via_qr(self, qr_image: Path, amount: str) -> "SendMoneyPage":
        a = self.actions
        a.tap(VIA_QR)
        self._push_to_gallery(qr_image)
        a.tap(UPLOAD_QR)
        if not a.is_visible(NEWEST_PHOTO, 8):
            if not a.is_visible(UPLOAD_QR, 2):
                self.driver.back()  # picker is open but empty: close it
            if not a.is_visible(UPLOAD_QR, 2):
                a.tap(VIA_QR)  # back left the QR screen
            a.tap(UPLOAD_QR)
        a.tap(NEWEST_PHOTO)  # newest first, and the image pushed above is the newest
        a.tap(PICKER_DONE)
        prefilled = a.text(BANK_AMOUNT)
        if prefilled.strip() == "" or prefilled == "Amount":
            a.type(BANK_AMOUNT, amount)
            a.tap(ACCOUNT_NAME)
        a.tap(NEXT)
        return self

    def to_bayad_wallet(self, number: str, amount: str) -> "SendMoneyPage":
        self.actions.tap(TO_BAYAD_WALLET)
        self.actions.type(SEND_TO, number)
        self.actions.type(AMOUNT, amount)
        self.actions.tap(AMOUNT_HEADING)
        self.actions.tap(NEXT)
        return self

    def to_other_bank(self, account_number: str, account_name: str, bank_name: str,
                      amount: str) -> "SendMoneyPage":
        a = self.actions
        result = (UIA, f'new UiSelector().descriptionStartsWith("{bank_name}")')
        opens = 0
        while opens < BANK_LIST_ATTEMPTS and not self._search_bank(bank_name, result):
            self._back_to_menu()
            opens += 1
        a.wait_visible(result).click()  # list rows are not flagged clickable, so skip the clickable wait
        a.type(ACCOUNT_NO, account_number)
        a.type(ACCOUNT_NAME, account_name)
        self._hide_keyboard()  # the keyboard covers the Amount field on this form
        a.type(BANK_AMOUNT, amount)
        a.tap(ACCOUNT_NAME)  # blur: the amount is only committed when it loses focus
        a.tap(NEXT)
        return self

    def confirm(self) -> "SendMoneyPage":
        self.actions.tap(CONFIRM)
        return self

    def is_review_displayed(self, timeout: Optional[float] = None) -> bool:
        return self.actions.is_visible(REVIEW, timeout)

    def is_receipt_displayed(self, timeout: Optional[float] = None) -> bool:
        return self.actions.is_visible(SUCCESS, timeout)

    # --- helpers -----------------------------------------------------------------------
    def _hide_keyboard(self) -> None:
        try:
            self.driver.hide_keyboard()
        except WebDriverException:
            pass  # keyboard already hidden

    def _back_to_menu(self) -> None:
        for _ in range(3):
            if self.actions.is_visible(TO_OTHER_BANKS, 2):
                break
            self.driver.back()

    def _search_bank(self, bank_name: str, result) -> bool:
        a = self.actions
        a.tap(TO_OTHER_BANKS)
        a.wait_visible((UIA, 'new UiSelector().descriptionContains("Bank")'))
        a.tap(SEARCH_ICON)
        for _ in range(SEARCH_ATTEMPTS):
            a.type(BANK_SEARCH, bank_name)
            if a.is_visible(result, 4):
                return True
        return False

    def _push_to_gallery(self, image: Path) -> None:
        try:
            remote = GALLERY_DIR + image.name
            self.driver.push_file(remote, base64.b64encode(image.read_bytes()).decode("ascii"))
            self.driver.execute_script("mobile: broadcast", {
                "action": "android.intent.action.MEDIA_SCANNER_SCAN_FILE", "uri": f"file://{remote}"})
        except OSError as e:
            raise FrameworkException(f"Could not push QR image {image}") from e
