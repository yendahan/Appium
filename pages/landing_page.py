from __future__ import annotations

from typing import Any, Optional

from framework import locator_parser
from framework.config_manager import ConfigManager
from pages.base_page import BasePage


class LandingPage(BasePage):
    def __init__(self, driver: Any) -> None:
        super().__init__(driver)
        self._landing = locator_parser.parse(ConfigManager.get_instance().require("app.landing.locator"))

    def is_displayed(self, timeout: Optional[float] = None) -> bool:
        return self.actions.is_visible(self._landing, timeout)
