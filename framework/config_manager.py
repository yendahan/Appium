"""Layered configuration.

Precedence (highest first): explicit overrides (``--cfg key=value``), environment variable
(KEY_WITH_UNDERSCORES), device profile, env profile, defaults. Profiles are selected with
``--env`` (default "qa") and ``--device`` (default "emulator").
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, Mapping, Optional

from framework.exceptions import FrameworkException

DEFAULT_ENV = "qa"
DEFAULT_DEVICE = "emulator"
CONFIG_DIR = Path(__file__).resolve().parent.parent / "config"


def to_env_name(key: str) -> str:
    """appium.url -> APPIUM_URL (env vars cannot contain dots)."""
    return key.upper().replace(".", "_")


def _present(value: Optional[str]) -> bool:
    return value is not None and value.strip() != ""


def _blank_to_default(value: Optional[str], fallback: str) -> str:
    return value.strip() if _present(value) else fallback


def _parse_properties(path: Path) -> Dict[str, str]:
    props: Dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith(("#", "!")) or "=" not in line:
            continue
        key, value = line.split("=", 1)
        props[key.strip()] = value.strip()
    return props


class ConfigManager:
    _instance: Optional["ConfigManager"] = None

    def __init__(self, env: Optional[str] = None, device: Optional[str] = None,
                 overrides: Optional[Mapping[str, str]] = None) -> None:
        self._env = _blank_to_default(env, DEFAULT_ENV)
        self._device = _blank_to_default(device, DEFAULT_DEVICE)
        self._overrides = dict(overrides or {})
        self._merged: Dict[str, str] = {}
        # Later files override earlier keys.
        self._load(CONFIG_DIR / "default.properties")
        self._load(CONFIG_DIR / "env" / f"{self._env}.properties")
        self._load(CONFIG_DIR / "devices" / f"{self._device}.properties")

    # --- singleton -------------------------------------------------------------------
    @classmethod
    def configure(cls, env: Optional[str] = None, device: Optional[str] = None,
                  overrides: Optional[Mapping[str, str]] = None) -> "ConfigManager":
        """Builds the shared instance (called once from conftest)."""
        cls._instance = cls(env, device, overrides)
        return cls._instance

    @classmethod
    def get_instance(cls) -> "ConfigManager":
        if cls._instance is None:
            cls._instance = cls(os.environ.get("ENV"), os.environ.get("DEVICE"))
        return cls._instance

    # --- accessors -------------------------------------------------------------------
    @property
    def env(self) -> str:
        return self._env

    @property
    def device(self) -> str:
        return self._device

    def get(self, key: str) -> str:
        """Value using the precedence order, or "" when not configured (never None)."""
        override = self._overrides.get(key)
        if _present(override):
            return override.strip()
        from_env = os.environ.get(to_env_name(key))
        if _present(from_env):
            return from_env.strip()
        return self._merged.get(key, "").strip()

    def has(self, key: str) -> bool:
        return self.get(key) != ""

    def require(self, key: str) -> str:
        value = self.get(key)
        if not value:
            raise FrameworkException(
                f"Missing required config '{key}'. Set it in config/env/{self._env}.properties, "
                f"config/devices/{self._device}.properties, via --cfg {key}=..., or env var "
                f"{to_env_name(key)}.")
        return value

    def get_int(self, key: str) -> int:
        value = self.require(key)
        try:
            return int(value)
        except ValueError as e:
            raise FrameworkException(f"Config '{key}' must be an integer but was '{value}'") from e

    def get_float(self, key: str) -> float:
        value = self.require(key)
        try:
            return float(value)
        except ValueError as e:
            raise FrameworkException(f"Config '{key}' must be a number but was '{value}'") from e

    def get_boolean(self, key: str) -> bool:
        value = self.get(key)
        if value == "" or value.lower() == "false":
            return False
        if value.lower() == "true":
            return True
        raise FrameworkException(f"Config '{key}' must be true or false but was '{value}'")

    def get_seconds(self, key: str) -> float:
        """Mandatory positive integer setting, returned as seconds."""
        seconds = self.get_int(key)
        if seconds <= 0:
            raise FrameworkException(f"Config '{key}' must be > 0 but was {seconds}")
        return float(seconds)

    # --- internals -------------------------------------------------------------------
    def _load(self, path: Path) -> None:
        if not path.is_file():
            raise FrameworkException(
                f"Config file '{path.relative_to(CONFIG_DIR.parent)}' not found (unknown --env or --device profile?)")
        try:
            self._merged.update(_parse_properties(path))
        except OSError as e:
            raise FrameworkException(f"Unable to read '{path}'") from e
