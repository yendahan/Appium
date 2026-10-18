from __future__ import annotations

from pathlib import Path
from typing import Optional

from appium.webdriver.common.appiumby import AppiumBy

from pages.base_page import BasePage
from pages.qr_upload import upload_qr_from_gallery
from pages.send_money_page import (ACCOUNT_NAME, BANK_AMOUNT, CONFIRM, NEXT, REVIEW, SERVICES,
                                   SUCCESS)

PAY_VIA_QR = (AppiumBy.ACCESSIBILITY_ID, "Pay via QR")


class PayViaQrPage(BasePage):
    def open(self) -> "PayViaQrPage":
        self.actions.tap(SERVICES)
        self.actions.tap(PAY_VIA_QR)
        return self

    def pay(self, qr_image: Path, amount: str) -> "PayViaQrPage":
        """Scan `qr_image`; `amount` is typed only when the QR does not carry one (dynamic QR)."""
        a = self.actions
        upload_qr_from_gallery(a, self.driver, qr_image, PAY_VIA_QR)
        prefilled = a.text(BANK_AMOUNT)
        if prefilled.strip() == "" or prefilled == "Amount":
            a.type(BANK_AMOUNT, amount)
            a.tap(ACCOUNT_NAME)  # blur: the amount is only committed when it loses focus
        a.tap(NEXT)
        return self

    def confirm(self) -> "PayViaQrPage":
        self.actions.tap(CONFIRM)
        return self

    def is_review_displayed(self, timeout: Optional[float] = None) -> bool:
        return self.actions.is_visible(REVIEW, timeout)

    def is_receipt_displayed(self, timeout: Optional[float] = None) -> bool:
        return self.actions.is_visible(SUCCESS, timeout)
