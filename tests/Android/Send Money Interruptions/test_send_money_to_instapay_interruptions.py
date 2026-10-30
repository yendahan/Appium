"""Interrupts To Other Banks, Via QR and Pay via QR on the review step (safe) and right after CONFIRM (risky: a real Php 10 each, dynamic QRs).

pytest -m device "tests/Android/Send Money Interruptions" --env qa --device emulator
Runs only when this folder is named on the command line."""
import pytest

from framework.test_data_loader import TestDataLoader
from pages.send_money_page import NEXT
from tests.Android.interruption_helpers import (AWAY_SECONDS, FLOWS, NETWORK_ERROR_OK, NO_CONNECTION, RETURN_TIMEOUT, assert_resolves,
                                                assert_review_recovers, open_review, package_of)

pytestmark = pytest.mark.device
RISKY = pytest.mark.risky  # taps CONFIRM: sends a real Php 10 on staging
DATA = TestDataLoader.for_current_env()


@pytest.fixture(params=FLOWS)
def flow(request) -> str:
    return request.param


@pytest.fixture
def review(driver, flow):
    return open_review(driver, DATA, flow)


# --- Before CONFIRM: no money moves ---------------------------------------------------------------------------------------------
def test_flow_01_background_on_review(review):
    """FLOW-01: backgrounding the app on the review step keeps the review and nothing is sent."""
    review.actions.background_app(AWAY_SECONDS)
    assert_review_recovers(review)


def test_flow_02_kill_on_review(review, driver):
    """FLOW-02: killing and reopening the app on the review step sends nothing and starts clean."""
    review.actions.restart_app(package_of(driver))
    assert not review.is_receipt_displayed(2) and not review.is_in_progress_displayed(), "Nothing may be sent without CONFIRM"
    assert not review.is_review_displayed(3), "The review step must not survive a killed app"


def test_flow_03_lock_on_review(review, driver):
    """FLOW-03: locking and unlocking the device on the review step does not send and the app recovers.

    Another app (e.g. Google Photos' first-run screen) can come to the front on unlock on the emulator, so the Bayad app is
    brought back to the front the way a user reopens it."""
    a = review.actions
    a.lock_device()
    a.unlock_device()
    driver.activate_app(package_of(driver))
    assert_review_recovers(review)


def test_flow_04_back_from_review(review):
    """FLOW-04: the Back key on the review step goes back a step and sends nothing."""
    review.actions.press_back()
    assert not review.is_receipt_displayed(2) and not review.is_in_progress_displayed(), "Nothing may be sent by Back"
    assert not review.is_review_displayed(3), "Back should leave the review step"


# --- After CONFIRM: each sends a real Php 10 -----------------------------------------------------------------------------------
@RISKY
def test_flow_05_background_after_confirm(review, flow):
    """FLOW-05: backgrounding the app right after CONFIRM still ends on the receipt."""
    review.confirm()
    review.actions.background_app(AWAY_SECONDS)
    assert_resolves(review, f"flow05-{flow}-background")


@RISKY
def test_flow_06_network_off_after_confirm(review, flow):
    """FLOW-06: losing the network right after CONFIRM ends on a "no connection" popup (nothing sent) or on a receipt.

    The "No Connection Found" popup is left as it is: its TRY AGAIN button would retry the payment."""
    a = review.actions
    review.confirm()
    a.set_network(False)
    a.set_network(True)
    if a.is_visible(NO_CONNECTION, RETURN_TIMEOUT):
        a.screenshot(f"flow06-{flow}-noConnection", "RECEIPT")
        assert not review.is_receipt_displayed(2) and not review.is_in_progress_displayed(), "A failed CONFIRM must not show a receipt"
    elif a.is_visible(NETWORK_ERROR_OK, 2):
        a.screenshot(f"flow06-{flow}-networkError", "RECEIPT")
        a.tap(NETWORK_ERROR_OK)
        assert not review.is_receipt_displayed(2) and not review.is_in_progress_displayed(), "A failed CONFIRM must not show a receipt"
        # the app returns to the form (or stays on the review) with the entries kept, so the user can retry
        assert review.is_review_displayed(RETURN_TIMEOUT) or a.is_visible(NEXT, RETURN_TIMEOUT), \
            "The app should stay on the review step or the form so the user can retry"
    else:
        assert_resolves(review, f"flow06-{flow}-networkOff")


@RISKY
def test_flow_07_kill_after_confirm(review, driver, flow):
    """FLOW-07: killing the app right after CONFIRM, then reopening it, does not crash and leaves no half-open review."""
    review.confirm()
    review.actions.restart_app(package_of(driver))
    review.actions.screenshot(f"flow07-{flow}-afterKill", "RECEIPT")
    assert not review.is_review_displayed(3), "The review step must not survive a killed app"
