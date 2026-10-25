"""The Zephyr Scale test-case definitions for the device tests, one per test function.

Tests link to their case by *name* (see ``zephyr_reporter.resolve``), so results land on the right case in whichever
folder a run uses. A run creates the folder if it does not exist, and creates in it any of these cases it lacks.
Add a new test here and give it a ``@pytest.mark.zephyr`` marker.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Dict, List, NamedTuple, Optional, Tuple

Step = Tuple[str, str]  # (description, expected result)
TESTS_DIR = Path(__file__).resolve().parents[1] / "tests"


class Case(NamedTuple):
    name: str
    objective: str
    steps: List[Step]


APP = ("Open the app and accept the Privacy Notice", "The Welcome screen is displayed")
LOGIN_FORM = [APP, ("Tap Log in", "The login form is displayed")]
LOGIN = [APP, ("Tap Log in and sign in as the test user", "The Biometric Setup screen is offered"),
         ("Tap Maybe next time", "The home screen is displayed")]
LAUNCH = [("Launch the app", "The app opens"),
          ("Check the landing element configured for the app", "The landing element is visible")]
QR_TYPES = "QRP2P static and dynamic, QRP2M static and dynamic"
REVIEW = "The Payment Confirmation review step is displayed"
SENT = ("Tap CONFIRM", "The receipt shows 'Successfully Sent!' ('Send Money in Progress!' fails the test)")

CASES: Dict[str, Case] = {
    # --- app launch ---------------------------------------------------------------------------------------------
    "test_app_launch.py::test_app_launches_and_landing_element_is_visible": Case(
        "App Launch: app opens on the landing screen",
        "Positive: app launches and the configured landing element is visible.", LAUNCH),
    "test_app_launch.py::test_missing_element_is_not_visible": Case(
        "App Launch: a missing element is reported as not visible",
        "Negative: a non-existent element is reported as not visible, not as an error.",
        LAUNCH + [("Look for an element that does not exist on the screen",
                   "It is reported as not visible, without an error")]),
    "test_app_launch.py::test_short_wait_times_out_quickly": Case(
        "App Launch: a 1-second wait on a missing element returns promptly",
        "Boundary: a 1s wait on a missing element returns promptly (no hang).",
        [("Wait 1 second for an element that does not exist", "The wait ends and reports the element as not visible"),
         ("Measure how long the wait took", "It ended in under 10 seconds (no hang)")]),
    "test_app_launch.py::test_scroll_to_missing_text_returns_false": Case(
        "App Launch: scrolling to missing text stops and returns false",
        "Edge: scrolling to text that does not exist stops after the bound and returns false.",
        LAUNCH + [("Scroll to a text that does not exist (at most 2 swipes)",
                   "Scrolling stops after the limit and reports the text was not found")]),
    # --- login --------------------------------------------------------------------------------------------------
    "test_login.py::test_valid_credentials_reach_home": Case(
        "Login: valid credentials reach the home screen",
        "Positive: valid credentials reach the home screen.",
        LOGIN_FORM + [("Enter the test user's mobile number and password and tap LOG IN",
                       "The Biometric Setup screen is offered"),
                      ("Tap Maybe next time", "The home screen is displayed")]),
    "test_login.py::test_unknown_account_is_rejected": Case(
        "Login: unknown account is rejected and can be retried",
        "Negative: unknown account is rejected with an error and can be retried.",
        LOGIN_FORM + [("Enter an unknown mobile number and a password and tap LOG IN",
                       "'Incorrect username or password.' is shown"),
                      ("Tap TRY AGAIN", "The login form is displayed again"),
                      ("Check the screen", "The home screen is not reached")]),
    "test_login.py::test_wrong_password_is_rejected": Case(
        "Login: wrong password is rejected",
        "Negative: valid username with a wrong password never reaches home.",
        LOGIN_FORM + [("Enter the test user's mobile number with a wrong password and tap LOG IN",
                       "'Incorrect username or password.' is shown"),
                      ("Check the screen", "The home screen is not reached")]),
    "test_login.py::test_submit_is_disabled_until_both_fields_are_filled": Case(
        "Login: LOG IN stays disabled until both fields are filled",
        "Edge: LOG IN stays disabled for an empty form and for a half-filled form.",
        LOGIN_FORM + [("Check LOG IN with both fields empty", "LOG IN is disabled"),
                      ("Enter only a mobile number", "LOG IN is still disabled and the home screen is not reached")]),
    "test_login.py::test_mobile_field_is_limited_to_ten_characters": Case(
        "Login: mobile field is limited to 10 characters",
        "Boundary: the mobile field keeps at most 10 characters.",
        LOGIN_FORM + [("Enter an 11-digit mobile number (09123456789)",
                       "The field keeps only the first 10 digits")]),
    # --- registration -------------------------------------------------------------------------------------------
    "test_basic_account_registration.py::test_invalid_mobile_number_is_rejected": Case(
        "Basic Account: Registration: invalid mobile number is rejected",
        "Negative: a number starting with 0 shows the format error and cannot be submitted.",
        [APP, ("Enter the mobile number 0999999999", "'Invalid mobile number format' is shown"),
         ("Check the SIGN UP! button", "SIGN UP! stays disabled and the Verification Code screen is not reached")]),
    "test_basic_account_registration.py::test_already_registered_mobile_shows_login": Case(
        "Basic Account: Registration: already registered mobile number shows the login page",
        "Edge: a number that is already registered ends on the login page instead of creating an account.",
        [("Open the app, accept the Privacy Notice and enter the registered number 9764912641", "SIGN UP! is enabled"),
         ("Tap SIGN UP!", "The Verification Code screen is displayed"),
         ("Enter the OTP", "The login page is displayed")]),
    "test_basic_account_registration.py::test_register_with_valid_mobile_and_otp": Case(
        "Basic Account: Registration: new mobile number completes registration",
        "Positive: a new (not yet registered) number registers and reaches the success page.",
        [("Open the app, accept the Privacy Notice and enter a new mobile number", "SIGN UP! is enabled"),
         ("Tap SIGN UP! and enter the OTP", "Complete Your Profile is displayed"),
         ("Enter first name, last name and date of birth, tap SAVE DETAILS", "Create Your Password is displayed"),
         ("Enter a valid password in both fields and tap SUBMIT", "Customize Profile is displayed"),
         ("Upload an avatar, enter a nickname and tap NEXT",
          "The 'All set' success page with CONTINUE is displayed")]),
    "test_basic_account_upgrade.py::test_upgrade_account_after_registration": Case(
        "Basic Account: Upgrade Account: newly registered account submits its upgrade request",
        "Positive: a freshly registered Basic account completes the Upgrade Account steps and the request is submitted.",
        [("Log in with the newly registered number and tap Upgrade Now on the dashboard",
          "Wallet features and limits is displayed"),
         ("Tap UPGRADE NOW", "Profile Information is displayed"),
         ("Tap Next, then enter the place of birth and pick nationality, source of fund and nature of work",
          "Address Information is displayed"),
         ("Pick a province and city, enter a street and tap Next", "Identity Verification is displayed"),
         ("Pick the ID type, enter the ID number and tap Next", "The ID photo steps are displayed"),
         ("Take the front and back ID photos, a selfie and a video, submitting each", "Review Details is displayed"),
         ("Tap Submit", "'Application Submitted!' is displayed")]),
    # --- pay bills ----------------------------------------------------------------------------------------------
    "test_pay_bills.py::test_pay_bills_manila_water": Case(
        "Pay Bills: Manila Water payment shows a receipt",
        "Positive: Pay Bills accepts a valid Manila Water account (Php 30) and shows a receipt after CONFIRM.",
        LOGIN + [("Tap Services, then Pay Bills, and wait for the billers to load", "The biller categories are displayed"),
                 ("Tap the search button, search Manila Water and open it",
                  "The Enter Biller Information form is displayed"),
                 ("Enter nickname, account number 12358959 and amount 30, then tap NEXT",
                  "Payment Summary shows total Php 40.00 (Php 30 + Php 10 fee)"),
                 ("Tap CONFIRM", "The receipt shows 'Payment Successful!'")]),
    # --- pay via QR ---------------------------------------------------------------------------------------------
    "test_pay_via_qr.py::test_pay_via_qr_valid": Case(
        "Pay via QR: valid QR code is accepted",
        f"Positive: Pay via QR accepts a valid QR code scanned from the gallery ({QR_TYPES}).",
        LOGIN + [("Open Pay via QR and upload the QR code from the gallery", "The review step is displayed"),
                 ("Tap CONFIRM", "The receipt shows the payment was completed")]),
    # --- send money (from Services) -----------------------------------------------------------------------------
    "test_send_money.py::test_via_qr_valid": Case(
        "Send Money: Via QR accepts a valid QR code",
        f"Positive: Via QR accepts a valid QR code ({QR_TYPES}).",
        LOGIN + [("Tap Services > Send Money > Via QR, upload the QR code from the gallery, enter amount 10 if the "
                  "QR has none and tap NEXT", REVIEW), SENT]),
    "test_send_money.py::test_to_bayad_wallet_valid": Case(
        "Send Money: To Bayad Wallet accepts a valid registered number",
        "Positive: To Bayad Wallet accepts a valid registered number.",
        LOGIN + [("Tap Services > Send Money > To Bayad Wallet, enter a registered number and amount 10, tap NEXT",
                  REVIEW), SENT]),
    "test_send_money.py::test_to_other_bank_valid": Case(
        "Send Money: To Other Banks and E-Wallets accepts a valid PNB account",
        "Positive: To Other Banks and E-Wallets accepts a valid Philippine National Bank account.",
        LOGIN + [("Tap Services > Send Money > To Other Banks and E-Wallets, search and pick Philippine National Bank, "
                  "enter account number, account name and amount 10, tap NEXT", REVIEW), SENT]),
    # --- send money (from the Wallet tab) -----------------------------------------------------------------------
    "test_send_money_via_bayad_wallet.py::test_wallet_via_qr_valid": Case(
        "Send Money from Wallet: Via QR accepts a valid QR code",
        f"Positive: from the Wallet tab, Send Money Via QR accepts a valid QR code ({QR_TYPES}).",
        LOGIN + [("Open Send Money from the Wallet tab, choose Via QR and upload the QR code",
                  "The review step is displayed"), SENT]),
    "test_send_money_via_bayad_wallet.py::test_wallet_to_bayad_wallet_valid": Case(
        "Send Money from Wallet: To Bayad Wallet accepts a valid registered number",
        "Positive: from the Wallet tab, To Bayad Wallet accepts a valid registered number.",
        LOGIN + [("Open Send Money from the Wallet tab, choose To Bayad Wallet and enter a registered number and amount",
                  "The review step is displayed"), SENT]),
    "test_send_money_via_bayad_wallet.py::test_wallet_to_other_bank_valid": Case(
        "Send Money from Wallet: To Other Banks and E-Wallets accepts a valid PNB account",
        "Positive: from the Wallet tab, To Other Banks and E-Wallets accepts a valid Philippine National Bank account.",
        LOGIN + [("Open Send Money from the Wallet tab, choose To Other Banks and E-Wallets and enter the account "
                  "details", "The review step is displayed"), SENT]),
}


# --- Upgraded Consumer Account: Wallet transactions (copied for Asenso below) ---------------------------------------------
WALLET_ACTIVITY = LOGIN + [("Tap the Wallet tab and tap See all", "The Transaction History and Ongoing Activities tabs are displayed")]
CASES.update({
    "test_wallet_transactions.py::test_wallet_transaction_history": Case(
        "Wallet: Transaction History is shown from See all",
        "Positive: Wallet > See all opens Activity; Transaction History shows its list or the empty message.",
        WALLET_ACTIVITY + [("Open Transaction History and take a screenshot",
                            "The history list or the empty message is displayed")]),
    "test_wallet_transactions.py::test_wallet_ongoing_activities": Case(
        "Wallet: Ongoing Activities is shown from See all",
        "Positive: Wallet > See all opens Activity; Ongoing Activities shows its list or the empty message.",
        WALLET_ACTIVITY + [("Open Ongoing Activities and take a screenshot",
                            "The activities list or the empty message is displayed")]),
})


# The same cases for the "Consumer Account with Asenso" test files (test_asenso_*.py); names are prefixed so they stay unique.
CASES.update({
    key.replace("test_", "test_asenso_", 1): Case(f"Asenso {case.name}", case.objective, case.steps)
    for key, case in list(CASES.items())
    if not key.startswith("test_basic_account_")  # Basic Account tests have no Asenso copy
})


# --- Asenso Account (the Asenso service, opened from Services > See All) ---------------------------------------------
ASENSO_OPEN = LOGIN + [("Tap Services > See All, scroll down and tap Asenso (Business)",
                        "The Asenso Wallet screen is displayed")]
CONFIRMATION = "The Transaction Confirmation screen is displayed"
SUCCESS = ("Tap CONFIRM", "The receipt shows a success message")
CASES.update({
    "test_asenso_account_add_money.py::test_add_money_from_bayad_wallet": Case(
        "Asenso Account: Add Money from My Bayad Wallet accepts Php 300",
        "Positive: Add Money from My Bayad Wallet moves Php 300 into the Asenso Wallet.",
        ASENSO_OPEN + [("Tap Add Money, choose From My Bayad Wallet, enter 300 and tap NEXT", CONFIRMATION), SUCCESS]),
    "test_asenso_account_withdraw_money.py::test_withdraw_money_to_bayad_wallet": Case(
        "Asenso Account: Withdraw Money to My Bayad Wallet accepts Php 300",
        "Positive: Withdraw Money to My Bayad Wallet moves Php 300 out of the Asenso Wallet.",
        ASENSO_OPEN + [("Tap Withdraw Money, choose To My Bayad Wallet, enter 300 and tap NEXT", CONFIRMATION), SUCCESS]),
    "test_asenso_account_pay_bills.py::test_asenso_pay_bills_manila_water": Case(
        "Asenso Account: Pay Bills with a Manila Water account shows a receipt",
        "Positive: Pay Bills from the Asenso screen accepts a valid Manila Water account (Php 30) and shows a receipt.",
        ASENSO_OPEN + [("Tap Pay Bills and wait for the billers to load", "The biller categories are displayed"),
                       ("Tap the search button, search Manila Water and open it",
                        "The Enter Biller Information form is displayed"),
                       ("Enter nickname, account number 12358959 and amount 30, then tap NEXT",
                        "Payment Summary shows total Php 40.00 (Php 30 + Php 10 fee)"),
                       ("Tap CONFIRM", "The receipt shows 'Payment Successful!'")]),
    "test_asenso_account_my_transactions.py::test_my_transactions_shows_history": Case(
        "Asenso Account: my transactions shows the transaction history",
        "Positive: my transactions opens Activity on the Transaction History tab with entries.",
        ASENSO_OPEN + [("Tap my transactions", "Activity opens on the Transaction History tab"),
                       ("Check the list", "At least one transaction is listed")]),
    "test_asenso_account_account_management.py::test_account_management_links_open_their_screens": Case(
        "Asenso Account: every Account Management link opens its screen",
        "Positive: each Account Management link opens its own screen and Back returns to the list.",
        ASENSO_OPEN + [("Tap the avatar left of the name", "Account Management is displayed"),
                       ("Tap each link (InstaPay Settings, Input Distributor Code, Upload Business Permit, Terms and "
                        "Conditions, Data Privacy, User Manual) and then Back",
                        "Each link opens its own screen and Back returns to Account Management"),
                       ("Check the FAQ link", "The FAQ link is listed")]),
})


# --- Basic Account (a Basic, not upgraded, consumer account) ------------------------------------------------------
CASES.update({
    "test_basic_account_add_money.py::test_over_the_counter_accepts_the_minimum_amount": Case(
        "Basic Account: Add Money Over the Counter accepts Php 300",
        "Positive: Add Money > Over the Counter > Bayad Center accepts the minimum amount (Php 300) and reaches "
        "Payment Confirmation (CONFIRM is not tapped).",
        LOGIN + [("Tap Add Money, choose Over the Counter and Bayad Center", "The amount form is displayed"),
                 ("Enter 300 and tap NEXT", "The Payment Confirmation screen is displayed")]),
    "test_basic_account_add_money.py::test_over_the_counter_below_minimum_shows_an_error": Case(
        "Basic Account: Add Money Over the Counter below the minimum shows an error",
        "Negative: an amount under the Php 300 minimum shows the minimum cash-in error and cannot be submitted.",
        LOGIN + [("Tap Add Money, choose Over the Counter and Bayad Center", "The amount form is displayed"),
                 ("Enter 100", "'The minimum cash-in amount is 300.' is shown"),
                 ("Check NEXT", "NEXT stays disabled")]),
    "test_basic_account_pay_bills.py::test_basic_pay_bills_manila_water": Case(
        "Basic Account: Pay Bills with a Manila Water account shows a receipt",
        "Positive: Pay Bills accepts a valid Manila Water account (Php 30) and shows a receipt after CONFIRM.",
        LOGIN + [("Tap Services, then Pay Bills, and wait for the billers to load", "The biller categories are displayed"),
                 ("Tap the search button, search Manila Water and open it",
                  "The Enter Biller Information form is displayed"),
                 ("Enter nickname, account number 12358959 and amount 30, then tap NEXT",
                  "Payment Summary shows total Php 40.00 (Php 30 + Php 10 fee)"),
                 ("Tap CONFIRM", "The receipt shows 'Payment Successful!'")]),
    "test_basic_account_login.py::test_login_with_biometrics_after_enabling_it": Case(
        "Basic Account: Login: biometrics enabled at setup logs in with the fingerprint on the next launch",
        "Positive: biometrics enabled on the Biometric Setup screen lets the next app launch log in with the fingerprint.",
        [APP, ("Tap Log in and sign in as the Basic test user", "The Biometric Setup screen is offered"),
         ("Tap GAME! and YES on the Enable Biometrics Authentication dialog", "The fingerprint prompt is displayed"),
         ("Touch the enrolled fingerprint", "The home screen is displayed"),
         ("Close and reopen the app", "The fingerprint prompt is displayed instead of the login form"),
         ("Touch the enrolled fingerprint", "The home screen is displayed")]),
    "test_basic_account_transactions.py::test_transaction_history_and_ongoing_activities_screenshots": Case(
        "Basic Account: Transaction History and Ongoing Activities are shown and captured",
        "Positive: the Activity tab shows Transaction History and Ongoing Activities; a screenshot is saved of each.",
        LOGIN + [("Tap the Activity tab", "The Transaction History and Ongoing Activities tabs are displayed"),
                 ("Open Transaction History and take a screenshot", "The history list or the empty message is displayed"),
                 ("Open Ongoing Activities and take a screenshot", "The activities list or the empty message is displayed")]),
})


def case_for(nodeid: str) -> Optional[Case]:
    """The case definition for a pytest node id such as ``tests/Android/Upgraded Consumer Account/test_login.py::test_x[param]``."""
    path, _, rest = nodeid.partition("::")
    function = rest.split("[", 1)[0]
    return CASES.get(f"{path.rsplit('/', 1)[-1]}::{function}")


# Where a failure happened: (text in the failure message, text in the expected result of the step it belongs to).
# Matching is case-insensitive; the first hint whose message text is found and whose step exists wins.
FAILURE_HINTS: List[Tuple[str, str]] = [
    ("Landing element", "landing element is visible"), ("precondition", "landing element is visible"),
    ("waited", "under 10 seconds"),
    ("Privacy notice should be", "welcome screen"), ("Welcome screen should offer", "welcome screen"),
    ("Login form should be displayed", "login form is displayed"),
    ("Biometric setup is offered", "biometric setup"), ("Home screen should show", "home screen is displayed"),
    ("Incorrect username or password", "incorrect username or password"),
    ("TRY AGAIN should return", "login form is displayed again"), ("Must not reach home", "home screen is not reached"),
    ("Empty form must not", "log in is disabled"), ("Mobile only must not", "still disabled"),
    ("Invalid mobile number format", "invalid mobile number format"),
    ("must stay disabled", "sign up! stays disabled"), ("Must not reach the verification", "sign up! stays disabled"),
    ("Verification Code screen should show", "verification code screen is displayed"),
    ("Login page should show", "login page is displayed"),
    ("Complete Your Profile should show", "complete your profile is displayed"),
    ("SAVE DETAILS should enable", "create your password is displayed"),
    ("Create Your Password should show", "create your password is displayed"),
    ("SUBMIT should enable", "customize profile is displayed"),
    ("Customize Profile should show", "customize profile is displayed"),
    ("NEXT should enable", "'all set' success page"), ("Almost there", "'all set' success page"),
    ("Success page should", "'all set' success page"),
    ("'WATER'", "biller categories"), ("Preferred Biller Nickname", "enter biller information"),
    ("Payment Summary should show", "payment summary"),
    ("should reach the review step", "review step"),
    ("Asenso Wallet", "asenso wallet screen"), ("Account Management should show", "account management is displayed"),
    ("Transaction Confirmation should show", "transaction confirmation"),
    ("Receipt should show a success", "success message"),
    ("Transaction History", "transaction history tab"), ("at least one transaction", "at least one transaction"),
    ("should open", "opens its own screen"), ("Back from", "opens its own screen"),
    ("Payment Confirmation should show", "payment confirmation screen"),
    ("minimum cash-in error", "minimum cash-in amount is 300"), ("NEXT must stay disabled", "next stays disabled"),
    ("Transaction History should show", "history list or the empty message"),
    ("Ongoing Activities should show", "activities list or the empty message"),
    ("Payment Successful!", "'payment successful!'"), ("Successfully Sent!", "'successfully sent!'"),
]


def failing_step(error: str, expected_results: List[str]) -> Optional[int]:
    """Index of the step a failure belongs to, found from the failure text; None if it can't be told."""
    message = error.lower()
    for in_message, in_expected in FAILURE_HINTS:
        if in_message.lower() in message:
            for i, expected in enumerate(expected_results):
                if in_expected in (expected or "").lower():
                    return i
    return None


@lru_cache(maxsize=1)
def _test_file_folders() -> Dict[str, str]:
    """Test file name -> its folder under tests/ (e.g. "Android/Upgraded Consumer Account"); unit tests are skipped."""
    folders: Dict[str, str] = {}
    for path in TESTS_DIR.rglob("test_*.py"):
        parts = path.parent.relative_to(TESTS_DIR).parts
        if parts and parts[0] != "unit":
            folders[path.name] = "/".join(parts)
    return folders


def folder_of(case_id: str) -> str:
    """The sub-folder of a test (a registry id or a pytest node id): where its file sits under tests/."""
    return _test_file_folders().get(Path(case_id.partition("::")[0]).name, "")


def groups() -> Dict[str, List[Case]]:
    """The defined cases grouped by Zephyr sub-folder, e.g. {"Android/Upgraded Consumer Account": [...]}."""
    grouped: Dict[str, List[Case]] = {}
    for case_id, case in CASES.items():
        grouped.setdefault(folder_of(case_id), []).append(case)
    return grouped
