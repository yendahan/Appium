from __future__ import annotations

import base64
from pathlib import Path
from typing import Any

from appium.webdriver.common.appiumby import AppiumBy

from framework.exceptions import FrameworkException
from framework.mobile_actions import MobileActions

UPLOAD_QR = (AppiumBy.ACCESSIBILITY_ID, "Upload QR from Gallery")
NEWEST_PHOTO = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().descriptionStartsWith("Photo taken").instance(0)')
PICKER_DONE = (AppiumBy.XPATH, "//*[@text='Done' or @content-desc='Done']")

GALLERY_DIR = "/sdcard/Pictures/"


def upload_qr_from_gallery(actions: MobileActions, driver: Any, image: Path, qr_screen) -> None:
    """Push `image` to the gallery and pick it through "Upload QR from Gallery".

    `qr_screen` is the locator that reopens the QR screen if Back closes it while recovering from an empty picker.
    """
    _push_to_gallery(driver, image)
    actions.tap(UPLOAD_QR)
    if not actions.is_visible(NEWEST_PHOTO, 8):
        if not actions.is_visible(UPLOAD_QR, 2):
            driver.back()  # picker is open but empty: close it
        if not actions.is_visible(UPLOAD_QR, 2):
            actions.tap(qr_screen)  # back left the QR screen
        actions.tap(UPLOAD_QR)
    actions.tap(NEWEST_PHOTO)  # newest first, and the image pushed above is the newest
    actions.tap(PICKER_DONE)


def _push_to_gallery(driver: Any, image: Path) -> None:
    try:
        remote = GALLERY_DIR + image.name
        driver.push_file(remote, base64.b64encode(image.read_bytes()).decode("ascii"))
        driver.execute_script("mobile: broadcast", {
            "action": "android.intent.action.MEDIA_SCANNER_SCAN_FILE", "uri": f"file://{remote}"})
    except OSError as e:
        raise FrameworkException(f"Could not push QR image {image}") from e
