"""WARNING: completes six real sends on staging (Php 6,000 To Other Banks and Php 60,000 To Bayad Wallet; keep the account funded).

OTP_MOBILE=9xxxxxxxxx OTP_PASSWORD=... pytest -m device "tests/Android/OTP Sending Money"
Scenarios of TOP_Instapay_Bayad_Wallet_Test_Scenarios.xlsx: the transaction OTP must not show below the trigger (Php 2,000 To Other Banks,
Php 20,000 To Bayad Wallet) and must show at and above it. OTP_CODE overrides the default test OTP (111111)."""
import os

import pytest

from framework.test_data_loader import TestDataLoader
from pages.send_money_page import ANY_RECEIPT, SendMoneyPage
from pages.verification_page import VerificationPage
from tests.Android.helpers import log_in_to_home

OTP_ACCOUNT = "otpAccount"  # testdata node: OTP_MOBILE / OTP_PASSWORD

pytestmark = [pytest.mark.device, pytest.mark.risky, pytest.mark.shared_session(OTP_ACCOUNT)]

REVIEW_TIMEOUT = 60
OTP_TIMEOUT = 30
COMPLETE_TIMEOUT = 90  # InstaPay transfers take 45s+
DEFAULT_OTP = "111111"
DATA = TestDataLoader.for_current_env()


@pytest.fixture
def send_money(driver) -> SendMoneyPage:
    log_in_to_home(driver, DATA, OTP_ACCOUNT)
    return SendMoneyPage(driver).open()


def to_other_bank(page: SendMoneyPage, amount: str) -> None:
    bank = DATA.node("sendMoney")["otherBank"]
    page.to_other_bank(bank["accountNumber"], bank["accountName"], bank["bankName"], amount)


def to_bayad_wallet(page: SendMoneyPage, amount: str) -> None:
    number = DATA.node("sendMoney")["bayadWalletNumber"]["asenso"]
    assert number != DATA.node(OTP_ACCOUNT)["username"], "OTP_MOBILE must not be the recipient wallet number"
    page.to_bayad_wallet(number, amount)


def assert_sent(page: SendMoneyPage, name: str) -> None:
    sent = page.is_receipt_displayed(COMPLETE_TIMEOUT)
    page.actions.screenshot(name, "RECEIPT")
    assert not (not sent and page.is_in_progress_displayed()), \
        "Receipt shows 'Send Money in Progress!' instead of 'Successfully Sent!'"
    assert sent, "Receipt should show 'Successfully Sent!'"


def otp_shown_after_confirm(page: SendMoneyPage, otp: VerificationPage, expect_otp: bool) -> bool:
    """True when the OTP screen shows after CONFIRM. Waits for it when it is expected; otherwise stops as soon as the receipt shows."""
    for _ in range(OTP_TIMEOUT):
        if otp.is_displayed(1):
            return True
        if not expect_otp and page.actions.is_visible(ANY_RECEIPT, 1):
            return False
    return False


def send(page: SendMoneyPage, name: str, expect_otp: bool) -> None:
    """CONFIRM, then the OTP is entered when the amount triggers it, then the receipt shows.

    The screen is recorded from before CONFIRM to the end of the send (saved in VIDEO, also when the test fails) and the screen right after
    CONFIRM is captured either way: in PASSED when the OTP showed as expected, in FAILED when it showed (or not) against the threshold."""
    actions = page.actions
    actions.start_recording()
    try:
        assert page.is_review_displayed(REVIEW_TIMEOUT), "The review step should show"
        page.confirm()
        otp = VerificationPage(page.driver)
        shown = otp_shown_after_confirm(page, otp, expect_otp)
        actions.screenshot(f"{name}-{'otp' if shown else 'noOtp'}", "PASSED" if shown == expect_otp else "FAILED")
        assert shown == expect_otp, ("The OTP should show at or above the trigger amount" if expect_otp
                                     else "The OTP must not show below the trigger amount")
        if shown:
            otp.enter_code(os.environ.get("OTP_CODE", "").strip() or DEFAULT_OTP)
        assert_sent(page, name)
    finally:
        actions.stop_recording(name, "VIDEO")


def test_top_01_below_trigger_other_bank(send_money):
    """TOP-01: Php 1,999.99 To Other Banks does not trigger the OTP."""
    to_other_bank(send_money, DATA.node("otpSend")["belowBank"])
    send(send_money, "top01-belowBank", expect_otp=False)


def test_top_02_at_trigger_other_bank(send_money):
    """TOP-02: Php 2,000 To Other Banks triggers the OTP."""
    to_other_bank(send_money, DATA.node("otpSend")["atBank"])
    send(send_money, "top02-atBank", expect_otp=True)


def test_top_03_above_trigger_other_bank(send_money):
    """TOP-03: Php 2,000.01 To Other Banks triggers the OTP."""
    to_other_bank(send_money, DATA.node("otpSend")["aboveBank"])
    send(send_money, "top03-aboveBank", expect_otp=True)


def test_bw_01_below_trigger_wallet(send_money):
    """BW-01: Php 19,999.99 To Bayad Wallet does not trigger the OTP."""
    to_bayad_wallet(send_money, DATA.node("otpSend")["belowWallet"])
    send(send_money, "bw01-belowWallet", expect_otp=False)


def test_bw_02_at_trigger_wallet(send_money):
    """BW-02: Php 20,000 To Bayad Wallet triggers the OTP."""
    to_bayad_wallet(send_money, DATA.node("otpSend")["atWallet"])
    send(send_money, "bw02-atWallet", expect_otp=True)


def test_bw_03_above_trigger_wallet(send_money):
    """BW-03: Php 20,000.01 To Bayad Wallet triggers the OTP."""
    to_bayad_wallet(send_money, DATA.node("otpSend")["aboveWallet"])
    send(send_money, "bw03-aboveWallet", expect_otp=True)
