"""Reusable, explicitly-waiting UI actions. The only module that touches the driver; pages delegate here."""
from __future__ import annotations

import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Optional, Tuple

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

# One folder per test run (process), e.g. screenshots/2026-10-16_14-30-00/PASSED
RUN_FOLDER = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")


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

    def type(self, locator: Locator, text: str) -> None:
        if text is None:
            raise ValueError("text must not be None (use clear() to empty a field)")
        LOG.info("Type into %s (%d chars)", locator, len(text))  # value not logged: may be a secret
        field = self.wait_clickable(locator)
        field.click()  # focus first: Flutter/custom fields only register input once focused
        field.clear()
        field.send_keys(text)

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

    # --- artifacts ---------------------------------------------------------------------
    def screenshot(self, name: str, subfolder: Optional[str] = None) -> Path:
        """Saves a PNG under <artifacts.dir>/screenshots/<run>/[subfolder]/ and returns its path."""
        directory = Path(self._cfg.require("artifacts.dir")) / "screenshots" / RUN_FOLDER
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
