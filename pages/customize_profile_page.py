from __future__ import annotations

from pathlib import Path
from typing import Optional

from appium.webdriver.common.appiumby import AppiumBy

from pages.base_page import BasePage
from pages.registration_success_page import RegistrationSuccessPage
from pages.qr_upload import NEWEST_PHOTO, PICKER_DONE, push_to_gallery

TITLE = (AppiumBy.ACCESSIBILITY_ID, "Customize Profile")
HEADING = (AppiumBy.ACCESSIBILITY_ID, "Almost there!")
PHOTO_LIBRARY = (AppiumBy.ACCESSIBILITY_ID, "Photo Library")
CROP = (AppiumBy.ACCESSIBILITY_ID, "Crop")
NICKNAME = (AppiumBy.XPATH, "//android.widget.EditText[@hint='How do you want us to call you?']")
NEXT = (AppiumBy.ACCESSIBILITY_ID, "NEXT")

# The camera badge on the avatar circle exposes no element of its own (tapping the "Upload Avatar" label does
# nothing), so tap its position: about 62% across and 42% down.
CAMERA_BADGE_X, CAMERA_BADGE_Y = 0.62, 0.4225


class CustomizeProfilePage(BasePage):
    """Shown once the account is created (the step after Create Your Password)."""

    def is_displayed(self, timeout: Optional[float] = None) -> bool:
        return self.actions.is_visible(TITLE, timeout)

    def is_almost_there_shown(self, timeout: Optional[float] = None) -> bool:
        return self.actions.is_visible(HEADING, timeout)

    def upload_avatar(self, image: Path) -> "CustomizeProfilePage":
        """Pushes `image` to the gallery and picks it from Photo Library (newest photo), then crops."""
        push_to_gallery(self.driver, image)
        self.actions.tap_at(CAMERA_BADGE_X, CAMERA_BADGE_Y)
        self.actions.tap(PHOTO_LIBRARY)
        self.actions.tap(NEWEST_PHOTO)
        self.actions.tap(PICKER_DONE)
        self.actions.tap(CROP)
        return self

    def enter_nickname(self, nickname: str) -> "CustomizeProfilePage":
        self.actions.type(NICKNAME, nickname)
        self.actions.tap(HEADING)  # drop focus so the keyboard closes (hide_keyboard() acts as Back and leaves the screen)
        return self

    def is_next_enabled(self) -> bool:
        return self.actions.is_enabled(NEXT)

    def next(self) -> RegistrationSuccessPage:
        self.actions.tap(NEXT)
        return RegistrationSuccessPage(self.driver)
