from __future__ import annotations

import time
from pathlib import Path
from typing import Optional

from appium.webdriver.common.appiumby import AppiumBy

from pages.base_page import BasePage
from pages.qr_upload import upload_qr_from_gallery

A11Y = AppiumBy.ACCESSIBILITY_ID
XPATH = AppiumBy.XPATH
UIA = AppiumBy.ANDROID_UIAUTOMATOR

SERVICES = (A11Y, "Services")
SEND_MONEY = (A11Y, "Send Money")
# the Wallet page first renders a placeholder (Php 0.00, 50,000 limit) and Send Money then asks to upgrade
WALLET_LOADED = (UIA, 'new UiSelector().descriptionContains("Upgraded Account")')
WALLET_TAB = (UIA, 'new UiSelector().descriptionStartsWith("Wallet")')  # bottom tab, desc "Wallet\nTab 3 of 4"
VIA_QR = (A11Y, "Via QR")
TO_BAYAD_WALLET = (A11Y, "To Bayad Wallet")
TO_OTHER_BANKS = (A11Y, "To Other Banks and E-Wallets")
SEND_TO = (XPATH, "//android.widget.EditText[@hint='Send money to']")
AMOUNT = (XPATH, "//android.widget.EditText[@hint='Enter cash amount']")
ACCOUNT_NO = (XPATH, "//android.widget.EditText[@hint='Account No.']")
BANK_AMOUNT = (XPATH, "//android.widget.EditText[@hint='Amount']")
ACCOUNT_NAME = (XPATH, "//android.widget.EditText[@hint='Account Name']")
AMOUNT_HEADING = (A11Y, "Enter or Select Amount (Php)")
RECIPIENT_HEADING = (A11Y, "Recipient's Details")
SEARCH_ICON = (XPATH, "(//android.widget.Button)[2]")  # unlabeled, top right
BANK_SEARCH = (AppiumBy.CLASS_NAME, "android.widget.EditText")
# InstaPay transfers (e.g. dynamic QRP2M) show "Send Money in Progress!" while the bank credits the amount; that is not a pass.
SUCCESS = (XPATH, "//*[contains(@content-desc,'Successfully Sent')]")
IN_PROGRESS = (XPATH, "//*[contains(@content-desc,'Send Money in Progress')]")
ANY_RECEIPT = (XPATH, "//*[contains(@content-desc,'Successfully Sent') or contains(@content-desc,'Send Money in Progress')]")
# A bank row's description is "<name>\n<Bank|...>"; the heading and "Select bank or wallet" have no line break, so a row means the list has loaded.
BANK_ROWS = (XPATH, "//*[contains(@content-desc,'\n')]")
LOAD_ERROR_TRY_AGAIN = (A11Y, "TRY AGAIN")  # button of the "Oops! Endpoint request timed out" popup
# The To Bayad Wallet screen first draws a placeholder (balance "Php 0.00", amount section), then redraws ~2s later with the real balance
# and the recent numbers, dropping anything typed meanwhile. Loaded = the recent numbers, or a balance other than Php 0.00.
WALLET_FORM_LOADED = (XPATH, "//*[@content-desc='Recently used mobile number' or "
                             "(starts-with(@content-desc,'Send Money') and not(contains(@content-desc,'Php 0.00')))]")
CONFIRM = (A11Y, "CONFIRM")
NEXT = (A11Y, "NEXT")
REVIEW = (XPATH, "//*[@content-desc='Send Money Confirmation' or @content-desc='Payment Confirmation']")

WALLET_FORM_TIMEOUT = 30
WALLET_ENTRY_ATTEMPTS = 3
WALLET_AMOUNT_TIMEOUT = 5
BANK_LIST_TIMEOUT = 60  # the banks load from the backend
BANK_RESULT_TIMEOUT = 10


class SendMoneyPage(BasePage):
    def open(self) -> "SendMoneyPage":
        self.actions.tap(SERVICES)
        self.actions.tap(SEND_MONEY)
        return self

    def open_from_wallet(self) -> "SendMoneyPage":
        self.actions.tap(WALLET_TAB)
        self.actions.wait_visible(WALLET_LOADED)
        self.actions.tap(SEND_MONEY)
        return self

    def via_qr(self, qr_image: Path, amount: str) -> "SendMoneyPage":
        a = self.actions
        a.tap(VIA_QR)
        upload_qr_from_gallery(a, self.driver, qr_image, VIA_QR)
        prefilled = a.text(BANK_AMOUNT)
        if prefilled.strip() == "" or prefilled == "Amount":
            a.type(BANK_AMOUNT, amount)
            a.tap(ACCOUNT_NAME)
        a.tap(NEXT)
        return self

    def to_bayad_wallet(self, number: str, amount: str) -> "SendMoneyPage":
        a = self.actions
        a.tap(TO_BAYAD_WALLET)
        a.wait_visible(WALLET_FORM_LOADED, WALLET_FORM_TIMEOUT)
        for _ in range(WALLET_ENTRY_ATTEMPTS):
            a.type(SEND_TO, number)
            a.press_enter()  # Done on the number pad commits the number; the amount section is only stable after that
            if not a.is_visible(AMOUNT, WALLET_AMOUNT_TIMEOUT):
                continue
            a.type(AMOUNT, amount)
            a.tap(AMOUNT_HEADING)
            # the form redraws a few times after the number is entered and drops what was typed meanwhile: check the amount stuck
            if a.is_visible(AMOUNT_HEADING, 2) and a.is_enabled(NEXT):
                break
        a.tap(NEXT)
        return self

    def to_other_bank(self, account_number: str, account_name: str, bank_name: str,
                      amount: str) -> "SendMoneyPage":
        a = self.actions
        result = (UIA, f'new UiSelector().descriptionStartsWith("{bank_name}")')
        self._search_bank(bank_name, result)
        a.wait_visible(result).click()  # list rows are not flagged clickable, so skip the clickable wait
        a.type(ACCOUNT_NO, account_number)
        a.press_enter()  # Done on the number pad: the Account Name field only shows once the account number is submitted
        a.type(ACCOUNT_NAME, account_name)
        a.press_enter()  # drop focus so the keyboard closes; the Recipient's Details heading is gone once the name shows
        a.type(BANK_AMOUNT, amount)
        a.press_enter()  # blur: the amount is only committed when it loses focus
        a.tap(NEXT)
        return self

    def confirm(self) -> "SendMoneyPage":
        self.actions.tap(CONFIRM)
        return self

    def is_review_displayed(self, timeout: Optional[float] = None) -> bool:
        return self.actions.is_visible(REVIEW, timeout)

    def is_receipt_displayed(self, timeout: Optional[float] = None) -> bool:
        """True only for the final "Successfully Sent!" receipt; "in progress" is not a success."""
        if not self.actions.is_visible(ANY_RECEIPT, timeout):
            return False
        return self.actions.is_visible(SUCCESS, 2)

    def is_in_progress_displayed(self) -> bool:
        return self.actions.is_visible(IN_PROGRESS, 2)

    # --- helpers -----------------------------------------------------------------------
    def _wait_for_bank_list(self) -> None:
        """Waits for the bank rows (the heading and search icon show before them); taps TRY AGAIN on the timeout popup."""
        a = self.actions
        deadline = time.monotonic() + BANK_LIST_TIMEOUT
        while not a.is_visible(BANK_ROWS, 2):
            if a.is_visible(LOAD_ERROR_TRY_AGAIN, 1):
                a.tap(LOAD_ERROR_TRY_AGAIN)
            if time.monotonic() > deadline:
                a.wait_visible(BANK_ROWS, 1)  # raises with the usual "not visible" message

    def _search_bank(self, bank_name: str, result) -> None:
        a = self.actions
        a.tap(TO_OTHER_BANKS)
        self._wait_for_bank_list()
        a.tap(SEARCH_ICON)
        a.type(BANK_SEARCH, bank_name)
        a.wait_visible(result, BANK_RESULT_TIMEOUT)
