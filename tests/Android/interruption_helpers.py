"""Shared by the Send Money interruption tests: timeouts, the "check your internet" popup, the recovery check and the flow builders."""
from __future__ import annotations

from pathlib import Path

from appium.webdriver.common.appiumby import AppiumBy

from framework.test_data_loader import TestDataLoader
from pages.home_page import HomePage
from pages.pay_via_qr_page import PayViaQrPage
from pages.send_money_page import ANY_RECEIPT, SendMoneyPage
from tests.Android.helpers import log_in_to_home

REVIEW_TIMEOUT = 60
COMPLETE_TIMEOUT = 90  # InstaPay transfers take 45s+
RETURN_TIMEOUT = 15
AWAY_SECONDS = 10
ROOT = Path(__file__).resolve().parents[2]
NETWORK_ERROR_OK = (AppiumBy.XPATH, "//*[contains(@content-desc,'OK, GOT IT')]")  # button of the "Oops! ... check your internet" popup

NO_CONNECTION = (AppiumBy.XPATH, "//*[contains(@content-desc,'No Connection Found')]")  # popup with TRY AGAIN, which retries the payment

FLOWS = ["other_bank", "via_qr", "pay_via_qr"]


def package_of(driver) -> str:
    return driver.capabilities.get("appPackage") or driver.current_package


def assert_review_recovers(page: SendMoneyPage) -> None:
    """After the interruption the review is still there, or the app is cleanly back on a known screen; never a stuck or sent state."""
    assert not page.is_receipt_displayed(2) and not page.is_in_progress_displayed(), "Nothing may be sent without CONFIRM"
    assert page.is_review_displayed(RETURN_TIMEOUT) or HomePage(page.driver).is_displayed(RETURN_TIMEOUT), \
        "The app should return to the review step or to Home"


def assert_resolves(page: SendMoneyPage, name: str) -> None:
    """The send ends in a receipt (sent, or still in progress); a receipt is the only valid outcome of a CONFIRM."""
    shown = page.actions.is_visible(ANY_RECEIPT, COMPLETE_TIMEOUT)
    page.actions.screenshot(name, "RECEIPT")
    assert shown, "A receipt ('Successfully Sent' or 'in progress') should show after CONFIRM and the interruption"


def open_review(driver, data: TestDataLoader, flow: str) -> SendMoneyPage:
    """Logs in and reaches the review step of `flow` for Php 10 (dynamic QRs), without tapping CONFIRM. Returns a SendMoneyPage for the checks."""
    log_in_to_home(driver, data)
    send = data.node("sendMoney")
    page = SendMoneyPage(driver)
    if flow == "other_bank":
        bank = send["otherBank"]
        page.open().to_other_bank(bank["accountNumber"], bank["accountName"], bank["bankName"], send["amount"])
    elif flow == "via_qr":
        page.open().via_qr(ROOT / send["qr"]["p2pDynamic"], send["amount"])
    elif flow == "pay_via_qr":
        PayViaQrPage(driver).open().pay(ROOT / send["qr"]["p2mDynamic"], send["amount"])
    else:
        raise ValueError(f"unknown flow {flow}")
    assert page.is_review_displayed(REVIEW_TIMEOUT), f"{flow} should reach the review step"
    return page
