"""Interrupts Send Money before CONFIRM (no money moves) and checks the app recovers.

pytest -m device "tests/Android/Send Money Interruptions" --env qa --device emulator
Runs only when this folder is named on the command line."""
import pytest
from selenium.common.exceptions import WebDriverException

from framework.test_data_loader import TestDataLoader
from pages.send_money_page import AMOUNT, CONFIRM, NEXT, SEND_TO, TO_BAYAD_WALLET, WALLET_FORM_LOADED, SendMoneyPage
from tests.Android.helpers import log_in_to_home
from tests.Android.interruption_helpers import (AWAY_SECONDS, NETWORK_ERROR_OK, RETURN_TIMEOUT, REVIEW_TIMEOUT, assert_resolves,
                                                assert_review_recovers)

pytestmark = pytest.mark.device
RISKY = pytest.mark.risky  # taps CONFIRM: sends a real Php 10 on staging

DATA = TestDataLoader.for_current_env()


@pytest.fixture
def send_money(driver) -> SendMoneyPage:
    log_in_to_home(driver, DATA)
    return SendMoneyPage(driver).open()


@pytest.fixture
def review(send_money) -> SendMoneyPage:
    """Send Money to the Asenso wallet number (Php 10), stopped on the review step."""
    send = DATA.node("sendMoney")
    send_money.to_bayad_wallet(send["bayadWalletNumber"]["asenso"], send["amount"])
    assert send_money.is_review_displayed(REVIEW_TIMEOUT), "The review step should show"
    return send_money


@pytest.fixture
def form(send_money) -> SendMoneyPage:
    """The To Bayad Wallet form with the recipient number typed, amount not yet entered."""
    a = send_money.actions
    a.tap(TO_BAYAD_WALLET)
    a.wait_visible(WALLET_FORM_LOADED, 30)
    a.type(SEND_TO, DATA.node("sendMoney")["bayadWalletNumber"]["asenso"])
    a.press_enter()
    assert a.is_visible(AMOUNT, 5), "The amount field should show once the number is entered"
    return send_money


def test_int_01_background_on_form(form):
    """INT-01: backgrounding the app on the Send Money form does not crash it; the form stays usable."""
    form.actions.background_app(AWAY_SECONDS)
    assert form.actions.is_visible(AMOUNT, RETURN_TIMEOUT) or form.actions.is_visible(SEND_TO, RETURN_TIMEOUT), \
        "The form should still show after the app returns"


def test_int_02_background_on_review(review):
    """INT-02: backgrounding the app on the review step keeps the review and nothing is sent."""
    review.actions.background_app(AWAY_SECONDS)
    assert_review_recovers(review)


def rotate_and_back(page: SendMoneyPage) -> None:
    """Rotates to landscape and back. The app is portrait-only (MainActivity requests SCREEN_ORIENTATION_PORTRAIT), so the
    device refusing the rotation is the expected outcome; if it does rotate, the screen must come back intact."""
    a = page.actions
    try:
        a.set_orientation("LANDSCAPE")
    except WebDriverException as e:
        assert "Screen rotation cannot be changed" in str(e), f"Unexpected rotation error: {e}"
        return
    finally:
        try:
            a.set_orientation("PORTRAIT")
        except WebDriverException:
            pass


def test_int_03_rotate_on_form(form):
    """INT-03: rotating the screen on the form (the app is portrait-locked) leaves the form usable."""
    rotate_and_back(form)
    assert form.actions.is_visible(AMOUNT, RETURN_TIMEOUT), "The amount field should still show after the rotation attempt"


def test_int_04_rotate_on_review(review):
    """INT-04: rotating the screen on the review step (the app is portrait-locked) keeps the review."""
    rotate_and_back(review)
    assert_review_recovers(review)


def test_int_05_lock_on_review(review, driver):
    """INT-05: locking and unlocking the device on the review step does not send and the app recovers.

    Another app (e.g. Google Photos' first-run screen) can come to the front on unlock on the emulator, so the Bayad app is brought back
    to the front the way a user reopens it before checking where it stands."""
    a = review.actions
    a.lock_device()
    a.unlock_device()
    driver.activate_app(driver.capabilities.get("appPackage") or driver.current_package)
    assert_review_recovers(review)


def test_int_06_kill_on_review(review, driver):
    """INT-06: killing and reopening the app on the review step sends nothing and starts clean (login or Home)."""
    package = driver.capabilities.get("appPackage") or driver.current_package
    review.actions.restart_app(package)
    assert not review.is_receipt_displayed(2) and not review.is_in_progress_displayed(), "Nothing may be sent without CONFIRM"
    assert not review.is_review_displayed(3), "The review step must not survive a killed app"


def test_int_07_back_from_review(review):
    """INT-07: the Back key on the review step goes back a step and sends nothing."""
    review.actions.press_back()
    assert not review.is_receipt_displayed(2) and not review.is_in_progress_displayed(), "Nothing may be sent by Back"
    assert not review.is_review_displayed(3), "Back should leave the review step"


def test_int_08_back_from_form(form):
    """INT-08: the Back key on the form leaves it without a crash."""
    form.actions.press_back()
    assert not form.actions.is_visible(NEXT, 3) or not form.actions.is_enabled(NEXT), "Back should leave the form or keep NEXT unavailable"


def test_int_09_network_off_on_next(form):
    """INT-09: with the network off, NEXT shows the "check your internet" popup (nothing sent) and the form works again once the network returns."""
    a = form.actions
    a.set_network(False)
    try:
        form._enter_amount(AMOUNT, DATA.node("sendMoney")["amount"])
        a.tap(NEXT)
        assert a.is_visible(NETWORK_ERROR_OK, RETURN_TIMEOUT), "A 'check your internet' popup should show when NEXT is tapped offline"
        assert not form.is_receipt_displayed(2) and not form.is_in_progress_displayed(), "Nothing may be sent without the network"
    finally:
        a.set_network(True)
    a.tap(NETWORK_ERROR_OK)
    assert a.is_visible(NEXT, RETURN_TIMEOUT), "The form should be usable again after the popup is closed"


# --- After CONFIRM: each of these sends a real Php 10 to the Asenso wallet number ---------------------------------------------
@RISKY
def test_int_10_double_tap_confirm(review):
    """INT-10: tapping CONFIRM twice quickly sends once and ends on one receipt."""
    a = review.actions
    button = a.wait_clickable(CONFIRM)
    button.click()
    try:
        button.click()
    except Exception:  # noqa: BLE001 - the button is gone once the first tap went through
        pass
    assert_resolves(review, "int10-doubleTap")


@RISKY
def test_int_11_background_after_confirm(review):
    """INT-11: backgrounding the app right after CONFIRM still ends on the receipt."""
    review.confirm()
    review.actions.background_app(AWAY_SECONDS)
    assert_resolves(review, "int11-background")


@RISKY
def test_int_12_network_off_after_confirm(review):
    """INT-12: losing the network right after CONFIRM ends on the "check your internet" popup (nothing sent) or on a receipt; never a stuck screen."""
    a = review.actions
    review.confirm()
    a.set_network(False)
    a.set_network(True)
    if a.is_visible(NETWORK_ERROR_OK, RETURN_TIMEOUT):
        a.screenshot("int12-networkError", "RECEIPT")
        a.tap(NETWORK_ERROR_OK)
        assert not review.is_receipt_displayed(2) and not review.is_in_progress_displayed(), "A failed CONFIRM must not show a receipt"
        # the app returns to the Send Money form with the number and amount kept, so the user can retry
        assert review.is_review_displayed(RETURN_TIMEOUT) or a.is_visible(NEXT, RETURN_TIMEOUT), \
            "The app should stay on the review step or the form so the user can retry"
    else:
        assert_resolves(review, "int12-networkOff")


@RISKY
def test_int_13_kill_after_confirm(review, driver):
    """INT-13: killing the app right after CONFIRM, then reopening it, does not crash and leaves no half-open review."""
    package = driver.capabilities.get("appPackage") or driver.current_package
    review.confirm()
    review.actions.restart_app(package)
    review.actions.screenshot("int13-afterKill", "RECEIPT")
    assert not review.is_review_displayed(3), "The review step must not survive a killed app"
