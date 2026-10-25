from __future__ import annotations

from typing import Optional

from appium.webdriver.common.appiumby import AppiumBy

from pages.base_page import BasePage

A11Y = AppiumBy.ACCESSIBILITY_ID
XPATH = AppiumBy.XPATH


def _starts_with(prefix: str):
    return XPATH, f"//*[starts-with(@content-desc,'{prefix}')]"


UPGRADE_NOW_BANNER = (A11Y, "Upgrade Now")  # on the Home dashboard
UPGRADE_NOW = (XPATH, "//android.widget.Button[@content-desc='UPGRADE NOW']")  # "Wallet features and limits" (the note above has a same-named text span)
NEXT = (A11Y, "Next")  # a disabled Button until the step is complete
PLACE_OF_BIRTH = (XPATH, "//android.widget.EditText[@hint='Place of Birth (City/Municipality)']")
NATIONALITY = (XPATH, "//android.widget.Button[starts-with(@content-desc,'Nationality')]")
SOURCE_OF_FUND = (XPATH, "//android.widget.Button[starts-with(@content-desc,'Source of Fund')]")
NATURE_OF_WORK = (XPATH, "//android.widget.Button[starts-with(@content-desc,'Nature of Work')]")
PROVINCE = (XPATH, "//android.widget.Button[starts-with(@content-desc,'Province/State')]")
CITY = (XPATH, "//android.widget.Button[starts-with(@content-desc,'City/Municipality')]")
STREET = (XPATH, "//android.widget.EditText[@hint='House No./Bldg No., Street, Subdivision']")
ID_TYPE = (XPATH, "//android.widget.Button[starts-with(@content-desc,'Choose ID Type')]")
ID_NUMBER = (XPATH, "//android.widget.EditText")  # the only field on the Identity Verification step
OK_GOT_IT = _starts_with("OK, GOT IT")
TAKE_BACK_PHOTO = (A11Y, "TAKE BACK PHOTO OF ID")
SUBMIT_AND_CONTINUE = _starts_with("SUBMIT &")
SUBMIT = (A11Y, "Submit")  # Review Details
SUBMITTED = (A11Y, "Application Submitted!")
ID_PREVIEW = (A11Y, "Nice shot!")
SELFIE_PREVIEW = _starts_with("That")  # "That's Cool!" (curly apostrophe)
VIDEO_PREVIEW = (A11Y, "Looking Great!")

PROFILE_STEP = (A11Y, "Profile Information")
ADDRESS_STEP = (A11Y, "Address Information")
IDENTITY_STEP = (A11Y, "Identity Verification")
REVIEW_STEP = (A11Y, "Review Details")

# The camera screens expose no usable elements, so the shutter is tapped by position: 50% across / 91.5% down.
SHUTTER_X, SHUTTER_Y = 0.5, 0.915

LOAD_TIMEOUT = 60  # each wizard step loads slowly
CAMERA_TIMEOUT = 60
SHOT_TIMEOUT = 15  # the preview shows within a few seconds of the shutter; a tap before the camera is ready is lost
SHOT_TRIES = 4
VIDEO_TIMEOUT = 40  # the video stops by itself after ~5s


class UpgradeAccountPage(BasePage):
    def start(self) -> "UpgradeAccountPage":
        """Home > Upgrade Now, then (once the limits page has loaded) UPGRADE NOW; ends on Profile Information."""
        a = self.actions
        a.tap(UPGRADE_NOW_BANNER)
        a.wait_visible(UPGRADE_NOW, LOAD_TIMEOUT)
        a.tap(UPGRADE_NOW)
        a.wait_visible(PROFILE_STEP, LOAD_TIMEOUT)
        return self

    def is_profile_step_displayed(self, timeout: Optional[float] = None) -> bool:
        return self.actions.is_visible(PROFILE_STEP, timeout)

    def continue_from_profile(self) -> "UpgradeAccountPage":
        """Step 1 (Customer's Name) is prefilled from the registration."""
        self.actions.tap(NEXT)
        return self

    def fill_other_information(self, place_of_birth: str, nationality: str, source_of_fund: str,
                               nature_of_work: str) -> "UpgradeAccountPage":
        """Step 2: the date of birth and mobile number are prefilled; the rest is typed or picked."""
        a = self.actions
        a.type(PLACE_OF_BIRTH, place_of_birth)
        a.press_enter()  # closes the keyboard
        self._pick(NATIONALITY, nationality)
        self._pick(SOURCE_OF_FUND, source_of_fund)
        self._pick(NATURE_OF_WORK, nature_of_work)
        a.tap(NEXT)
        return self

    def fill_address(self, province: str, city: str, street: str) -> "UpgradeAccountPage":
        """Step 3: the present address is also used as the permanent address (ticked by default)."""
        a = self.actions
        a.wait_visible(ADDRESS_STEP, LOAD_TIMEOUT)
        self._pick(PROVINCE, province)
        self._pick(CITY, city)  # lists the cities once a province is chosen
        a.type(STREET, street)
        a.press_enter()
        a.tap(NEXT)
        return self

    def choose_id(self, id_type: str, id_number: str) -> "UpgradeAccountPage":
        """Step 4: the ID type and number, then NEXT opens the photo steps."""
        a = self.actions
        a.wait_visible(IDENTITY_STEP, LOAD_TIMEOUT)
        self._pick(ID_TYPE, id_type)
        a.type(ID_NUMBER, id_number)
        a.press_enter()
        a.tap(NEXT)
        return self

    def capture_identity(self) -> "UpgradeAccountPage":
        """Identity Verification 1-3 of 3: the ID front and back photos, a selfie and a short video, all from the camera."""
        a = self.actions
        a.tap(OK_GOT_IT)  # "Take a photo of your ID"
        self._shoot(ID_PREVIEW)  # front
        a.tap(TAKE_BACK_PHOTO)
        self._shoot(ID_PREVIEW)  # back
        a.tap(SUBMIT_AND_CONTINUE)
        a.tap(OK_GOT_IT)  # "Take a selfie"
        self._shoot(SELFIE_PREVIEW)
        a.tap(SUBMIT_AND_CONTINUE)
        a.tap(OK_GOT_IT)  # "Shoot a 5-second video"
        self._shoot(VIDEO_PREVIEW, video=True)
        a.tap(SUBMIT_AND_CONTINUE)
        return self

    def is_review_displayed(self, timeout: Optional[float] = None) -> bool:
        return self.actions.is_visible(REVIEW_STEP, timeout)

    def submit(self) -> "UpgradeAccountPage":
        self.actions.tap(SUBMIT)
        return self

    def is_submitted(self, timeout: Optional[float] = None) -> bool:
        return self.actions.is_visible(SUBMITTED, timeout)

    def _pick(self, dropdown, option: str) -> None:
        """Opens a dropdown and taps `option` (its entries are exposed by their text)."""
        self.actions.tap(dropdown)
        self.actions.tap((A11Y, option))

    def _shoot(self, preview, video: bool = False) -> None:
        """Taps the camera shutter until `preview` shows (a video is started once and left to stop by itself)."""
        a = self.actions
        for _ in range(1 if video else SHOT_TRIES):
            a.tap_at(SHUTTER_X, SHUTTER_Y)
            if a.is_visible(preview, VIDEO_TIMEOUT if video else SHOT_TIMEOUT):
                return
        a.wait_visible(preview, 1)  # raises with the usual "not visible" message
