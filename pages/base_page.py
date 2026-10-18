from __future__ import annotations

from typing import Any

from framework.mobile_actions import MobileActions


class BasePage:
    """Pages hold locators only and delegate every interaction to MobileActions."""

    def __init__(self, driver: Any) -> None:
        self.driver = driver
        self.actions = MobileActions(driver)
