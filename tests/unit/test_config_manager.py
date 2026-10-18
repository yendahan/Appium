import pytest

from framework.config_manager import ConfigManager
from framework.exceptions import FrameworkException

pytestmark = pytest.mark.unit


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    for var in ("WAIT_EXPLICIT_SECONDS", "APPIUM_URL", "APP_NORESET"):
        monkeypatch.delenv(var, raising=False)


def test_loads_defaults_and_profiles():
    cfg = ConfigManager("qa", "emulator")
    assert cfg.get("appium.url") == "http://127.0.0.1:4723"
    assert cfg.get("device.name") == "Android Emulator"
    assert cfg.get_seconds("wait.explicit.seconds") == 15


def test_blank_profiles_fall_back_to_defaults():
    cfg = ConfigManager("  ", None)
    assert cfg.env == "qa"
    assert cfg.device == "emulator"


def test_override_beats_file():
    cfg = ConfigManager("qa", "physical", {"appium.url": "http://10.0.0.5:4723"})
    assert cfg.get("appium.url") == "http://10.0.0.5:4723"


def test_env_var_beats_file_but_override_beats_env_var(monkeypatch):
    monkeypatch.setenv("APPIUM_URL", "http://env:4723")
    assert ConfigManager("qa", "emulator").get("appium.url") == "http://env:4723"
    assert ConfigManager("qa", "emulator", {"appium.url": "http://cli:4723"}).get("appium.url") == "http://cli:4723"


def test_unset_optional_value_is_empty_not_none():
    cfg = ConfigManager("qa", "emulator")
    assert cfg.get("does.not.exist") == ""
    assert not cfg.has("does.not.exist")


def test_require_fails_fast_with_key_in_message():
    with pytest.raises(FrameworkException) as e:
        ConfigManager("qa", "emulator").require("does.not.exist")
    assert "does.not.exist" in str(e.value)
    assert "DOES_NOT_EXIST" in str(e.value)


def test_unknown_profile_is_rejected():
    with pytest.raises(FrameworkException):
        ConfigManager("nope", "emulator")
    with pytest.raises(FrameworkException):
        ConfigManager("qa", "nope")


def test_non_numeric_integer_is_rejected():
    cfg = ConfigManager("qa", "emulator", {"wait.explicit.seconds": "abc"})
    with pytest.raises(FrameworkException):
        cfg.get_int("wait.explicit.seconds")


@pytest.mark.parametrize("value", ["0", "-5"])
def test_zero_and_negative_timeouts_are_rejected(value):
    with pytest.raises(FrameworkException):
        ConfigManager("qa", "emulator", {"wait.explicit.seconds": value}).get_seconds("wait.explicit.seconds")


def test_smallest_valid_timeout():
    assert ConfigManager("qa", "emulator", {"wait.explicit.seconds": "1"}).get_seconds("wait.explicit.seconds") == 1


def test_boolean_parsing():
    cfg = ConfigManager("qa", "emulator")
    assert cfg.get_boolean("app.autoGrantPermissions") is True
    assert cfg.get_boolean("app.noReset") is False
    with pytest.raises(FrameworkException):
        ConfigManager("qa", "emulator", {"app.noReset": "maybe"}).get_boolean("app.noReset")
