"""Creates the Appium session from configuration."""
from __future__ import annotations

import logging
from typing import Any
from urllib.parse import urlparse

from appium import webdriver
from appium.options.android import UiAutomator2Options
from selenium.common.exceptions import SessionNotCreatedException

from framework.config_manager import ConfigManager
from framework.exceptions import FrameworkException

LOG = logging.getLogger(__name__)


def build_options(cfg: ConfigManager) -> UiAutomator2Options:
    options = UiAutomator2Options()
    options.device_name = cfg.require("device.name")
    options.new_command_timeout = cfg.get_seconds("session.newCommandTimeout.seconds")
    options.no_reset = cfg.get_boolean("app.noReset")
    options.auto_grant_permissions = cfg.get_boolean("app.autoGrantPermissions")
    if cfg.has("device.udid"):
        options.udid = cfg.get("device.udid")
    if cfg.has("device.avd"):
        options.avd = cfg.get("device.avd")
    if cfg.has("device.platformVersion"):
        options.platform_version = cfg.get("device.platformVersion")
    if cfg.has("app.path"):
        options.app = cfg.get("app.path")
    elif cfg.has("app.package") and cfg.has("app.activity"):
        options.app_package = cfg.get("app.package")
        options.app_activity = cfg.get("app.activity")
    else:
        raise FrameworkException(
            "App under test is not configured. Set app.path (APK) or both app.package and app.activity "
            f"for env '{cfg.env}'.")
    return options


def server_url(cfg: ConfigManager) -> str:
    raw = cfg.require("appium.url")
    parsed = urlparse(raw)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise FrameworkException(f"Invalid appium.url '{raw}'")
    return raw


def create(cfg: ConfigManager) -> Any:
    options = build_options(cfg)
    url = server_url(cfg)
    LOG.info("Creating Android session on %s (env=%s, device=%s)", url, cfg.env, cfg.device)
    try:
        driver = webdriver.Remote(url, options=options)
        driver.implicitly_wait(0)  # explicit waits only
        return driver
    except SessionNotCreatedException as e:
        raise FrameworkException(
            "Appium could not create a session. Check that the device/emulator is online (`adb devices`), "
            f"the UiAutomator2 driver is installed, and the app settings are correct. Server said: {e.msg}") from e
    except Exception as e:  # noqa: BLE001 - connection errors surface as several urllib3/selenium types
        raise FrameworkException(f"Could not reach Appium server at {url}. Is it running? ({e})") from e
