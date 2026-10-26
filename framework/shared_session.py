"""One Appium session (and login) shared by consecutive tests of the same account, for ``--reuse-app``."""
from __future__ import annotations

import logging
from typing import Any, Callable, Optional

LOG = logging.getLogger(__name__)


class SharedSession:
    def __init__(self, create: Callable[[], Any], return_to_home: Callable[[Any], bool]) -> None:
        self._create = create
        self._return_to_home = return_to_home
        self._driver: Optional[Any] = None
        self._key: Optional[str] = None

    def acquire(self, key: str) -> Any:
        """The open session when it is the same account and it got back to Home, else a fresh one."""
        if self._driver is not None and self._key == key and self._can_reuse():
            LOG.info("Reusing the open app session (%s)", key)
            return self._driver
        self.discard()
        self._driver, self._key = self._create(), key
        return self._driver

    def _can_reuse(self) -> bool:
        """True when the open session got back to Home; a session Appium already closed counts as not reusable."""
        try:
            return self._return_to_home(self._driver)
        except Exception as e:  # noqa: BLE001
            LOG.warning("The open app session is gone (%s), starting a fresh one", type(e).__name__)
            return False

    def discard(self) -> None:
        """Closes the session (after a failure, an account change, or the end of the run)."""
        driver, self._driver, self._key = self._driver, None, None
        if driver is None:
            return
        try:
            driver.quit()
        except Exception as e:  # noqa: BLE001
            LOG.warning("driver.quit() failed: %s", e)

    def owns(self, driver: Any) -> bool:
        return driver is not None and driver is self._driver
