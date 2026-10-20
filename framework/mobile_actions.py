"""Reusable, explicitly-waiting UI actions. The only module that touches the driver; pages delegate here."""
from __future__ import annotations

import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any, List, Optional, Tuple

from appium.webdriver.common.appiumby import AppiumBy
from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from framework import gesture_validator, locator_parser
from framework.config_manager import ConfigManager
from framework.exceptions import FrameworkException

LOG = logging.getLogger(__name__)
Locator = Tuple[str, str]

# One folder per test run (process), e.g. Screenshots/2026-10-16_14-30-00/PASSED
RUN_FOLDER = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")


_ILLEGAL_IN_FOLDER = re.compile(r'[<>:"|?*\x00-\x1f]')
_screenshot_subfolder = ""


def set_screenshot_subfolder(path: str) -> None:
    """Sets the folder (relative, "/"-separated) screenshots go in for the test that is running, e.g. the folders its
    test file sits in under tests/. The test runner sets it per test and clears it afterwards."""
    global _screenshot_subfolder
    _screenshot_subfolder = path or ""


def folder_parts(path: Optional[str]) -> List[str]:
    """Splits a "a/b" folder value into folder names, keeping spaces and dropping characters illegal in folder
    names and any "." / ".." part (so a value can never point outside the Screenshots folder)."""
    parts: List[str] = []
    for raw in re.split(r"[\\/]+", path or ""):
        part = _ILLEGAL_IN_FOLDER.sub("_", raw).strip().strip(".").strip()
        if part:
            parts.append(part)
    return parts


def sanitize(name: Optional[str]) -> str:
    clean = re.sub(r"[^A-Za-z0-9._-]", "_", name or "")
    return clean or "unnamed"


class MobileActions:
    def __init__(self, driver: Any, cfg: Optional[ConfigManager] = None) -> None:
        self.driver = driver
        self._cfg = cfg or ConfigManager.get_instance()
        self._default_timeout = self._cfg.get_seconds("wait.explicit.seconds")
        self._poll = self._cfg.get_int("wait.poll.millis") / 1000.0

    # --- waits -----------------------------------------------------------------------
    def wait_visible(self, locator: Locator, timeout: Optional[float] = None) -> WebElement:
        timeout = self._default_timeout if timeout is None else timeout
        try:
            return self._wait(timeout).until(EC.visibility_of_element_located(locator))
        except TimeoutException as e:
            raise FrameworkException(f"Element not visible within {timeout:g}s: {locator}") from e

    def wait_clickable(self, locator: Locator) -> WebElement:
        try:
            return self._wait(self._default_timeout).until(EC.element_to_be_clickable(locator))
        except TimeoutException as e:
            raise FrameworkException(
                f"Element not clickable within {self._default_timeout:g}s: {locator}") from e

    def is_visible(self, locator: Any, timeout: Optional[float] = None) -> bool:
        """True if visible within the timeout; a timeout is a normal 'no', not an error."""
        if isinstance(locator, str):
            locator = locator_parser.parse(locator)
        timeout = self._default_timeout if timeout is None else timeout
        try:
            self._wait(timeout).until(EC.visibility_of_element_located(locator))
            return True
        except TimeoutException:
            return False

    # --- interactions ------------------------------------------------------------------
    def tap(self, locator: Locator) -> None:
        LOG.info("Tap %s", locator)
        self.wait_clickable(locator).click()

    def tap_present(self, locator: Locator) -> None:
        """Taps an element that exists but is not reported visible/clickable (e.g. a Flutter field opening a picker)."""
        LOG.info("Tap (present) %s", locator)
        try:
            self._wait(self._default_timeout).until(EC.presence_of_element_located(locator)).click()
        except TimeoutException as e:
            raise FrameworkException(f"Element not present within {self._default_timeout:g}s: {locator}") from e

    def type(self, locator: Locator, text: str) -> None:
        if text is None:
            raise ValueError("text must not be None (use clear() to empty a field)")
        LOG.info("Type into %s (%d chars)", locator, len(text))  # value not logged: may be a secret
        field = self.wait_clickable(locator)
        field.click()  # focus first: Flutter/custom fields only register input once focused
        field.clear()
        field.send_keys(text)

    def tap_at(self, x_percent: float, y_percent: float) -> None:
        """Taps a screen point (fractions 0-1); for custom widgets that expose no usable element."""
        size = self.driver.get_window_size()
        self.driver.tap([(int(size["width"] * x_percent), int(size["height"] * y_percent))])

    def press_back(self) -> None:
        """The device Back key, for screens that have no Back button of their own."""
        LOG.info("Press device Back")
        self.driver.back()

    def press_digits(self, digits: str) -> None:
        """Sends digits as hardware key presses to the focused widget (value not logged: may be a code)."""
        if not digits.isdigit():
            raise ValueError("digits must contain only 0-9")
        LOG.info("Press %d digit keys", len(digits))
        for digit in digits:
            self.driver.press_keycode(7 + int(digit))  # KEYCODE_0 = 7

    def clear(self, locator: Locator) -> None:
        LOG.info("Clear %s", locator)
        self.wait_visible(locator).clear()

    def is_enabled(self, locator: Locator) -> bool:
        return self.wait_visible(locator).is_enabled()

    def text(self, locator: Locator) -> str:
        return self.wait_visible(locator).text

    # --- gestures ----------------------------------------------------------------------
    def swipe(self, direction: str, percent: Optional[float] = None) -> None:
        if percent is None:
            percent = self._cfg.get_float("swipe.defaultPercent")
        direction = gesture_validator.validate_direction(direction)
        gesture_validator.validate_percent(percent)
        size = self.driver.get_window_size()
        LOG.info("Swipe %s %d%% on %sx%s screen", direction, int(percent * 100), size["width"], size["height"])
        try:
            self.driver.execute_script("mobile: swipeGesture", {
                "left": int(size["width"] * 0.1), "top": int(size["height"] * 0.1),
                "width": int(size["width"] * 0.8), "height": int(size["height"] * 0.8),
                "direction": direction, "percent": percent})
        except WebDriverException as e:
            raise FrameworkException(f"Swipe {direction} failed") from e

    def scroll_to_text(self, text: str, max_swipes: Optional[int] = None) -> bool:
        """Scrolls the first scrollable container until the exact text shows; False if not found."""
        if text is None or text.strip() == "":
            raise ValueError("text must not be blank")
        if max_swipes is None:
            max_swipes = self._cfg.get_int("scroll.maxAttempts")
        gesture_validator.validate_max_attempts(max_swipes)
        selector = ("new UiScrollable(new UiSelector().scrollable(true).instance(0))"
                    f".setMaxSearchSwipes({max_swipes})"
                    f'.scrollIntoView(new UiSelector().text("{locator_parser.escape_ui_selector(text)}"))')
        try:
            self.driver.find_element(AppiumBy.ANDROID_UIAUTOMATOR, selector)
            return True
        except NoSuchElementException:
            LOG.warning("Text '%s' not found after %d swipes", text, max_swipes)
            return False

    def scroll_to_description(self, description: str, max_swipes: Optional[int] = None) -> bool:
        """Like scroll_to_text, but matches the accessibility description exactly (e.g. a year in a date picker)."""
        if description is None or description.strip() == "":
            raise ValueError("description must not be blank")
        if max_swipes is None:
            max_swipes = self._cfg.get_int("scroll.maxAttempts")
        gesture_validator.validate_max_attempts(max_swipes)
        selector = ("new UiScrollable(new UiSelector().scrollable(true).instance(0))"
                    f".setMaxSearchSwipes({max_swipes})"
                    f'.scrollIntoView(new UiSelector().description("{locator_parser.escape_ui_selector(description)}"))')
        try:
            self.driver.find_element(AppiumBy.ANDROID_UIAUTOMATOR, selector)
            return True
        except NoSuchElementException:
            LOG.warning("Description '%s' not found after %d swipes", description, max_swipes)
            return False

    # --- artifacts ---------------------------------------------------------------------
    def screenshot(self, name: str, subfolder: Optional[str] = None) -> Path:
        """Saves a PNG and returns its path.

        Path: <artifacts.dir>/Screenshots/<zephyr.cases.folder>/<folders of the test file under tests/>/<run>/
        [subfolder]/. The first two levels mirror the Zephyr folder tree and are left out when not set.
        """
        directory = Path(self._cfg.require("artifacts.dir")) / "Screenshots"
        for part in folder_parts(self._cfg.get("zephyr.cases.folder")) + folder_parts(_screenshot_subfolder):
            directory = directory / part
        directory = directory / RUN_FOLDER
        if subfolder and subfolder.strip():
            directory = directory / sanitize(subfolder)
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")[:-3]
        target = directory / f"{sanitize(name)}-{stamp}.png"
        try:
            directory.mkdir(parents=True, exist_ok=True)
            target.write_bytes(self.driver.get_screenshot_as_png())
            LOG.info("Screenshot saved: %s", target)
            return target
        except (OSError, WebDriverException) as e:
            raise FrameworkException(f"Could not capture screenshot '{name}'") from e

    def page_source(self) -> str:
        return self.driver.page_source

    # --- internals ---------------------------------------------------------------------
    def _wait(self, timeout: float) -> WebDriverWait:
        if timeout is None or timeout <= 0:
            raise ValueError(f"timeout must be positive but was {timeout}")
        return WebDriverWait(self.driver, timeout, poll_frequency=self._poll)
