"""Converts "strategy=value" strings from configuration into an (Appium by, value) tuple.

Supported strategies: id, accessibilityId, xpath, text (exact visible text), className.
"""
from __future__ import annotations

from typing import Optional, Tuple

from appium.webdriver.common.appiumby import AppiumBy

from framework.exceptions import FrameworkException

Locator = Tuple[str, str]


def escape_ui_selector(value: str) -> str:
    """Escape backslashes first so the backslashes added for quotes are not escaped twice."""
    return value.replace("\\", "\\\\").replace('"', '\\"')


def parse(raw: Optional[str]) -> Locator:
    if raw is None or raw.strip() == "":
        raise FrameworkException("Locator is empty. Expected format 'strategy=value'")
    # Split on the first '=' only: values (e.g. xpath) may contain further '=' characters.
    idx = raw.find("=")
    if idx <= 0:
        raise FrameworkException(f"Invalid locator '{raw}'. Expected format 'strategy=value'")
    strategy = raw[:idx].strip()
    value = raw[idx + 1:].strip()
    if not value:
        raise FrameworkException(f"Locator '{raw}' has an empty value")
    if strategy == "id":
        return (AppiumBy.ID, value)
    if strategy == "accessibilityId":
        return (AppiumBy.ACCESSIBILITY_ID, value)
    if strategy == "xpath":
        return (AppiumBy.XPATH, value)
    if strategy == "className":
        return (AppiumBy.CLASS_NAME, value)
    if strategy == "text":
        return (AppiumBy.ANDROID_UIAUTOMATOR, f'new UiSelector().text("{escape_ui_selector(value)}")')
    raise FrameworkException(
        f"Unsupported locator strategy '{strategy}' in '{raw}'. Use id, accessibilityId, xpath, className or text")
