import pytest
from appium.webdriver.common.appiumby import AppiumBy

from framework import locator_parser
from framework.exceptions import FrameworkException
from framework.test_data_loader import TestDataLoader

pytestmark = pytest.mark.unit

DATA = TestDataLoader("qa")
VALID = list(DATA.node("validLocators").items())
INVALID = DATA.node("invalidLocators") + [None]


@pytest.mark.parametrize("raw,strategy", VALID)
def test_parses_supported_strategies(raw, strategy):
    by, value = locator_parser.parse(raw)
    assert by and value, f"strategy {strategy}"


@pytest.mark.parametrize("raw", INVALID)
def test_rejects_malformed_locators(raw):
    with pytest.raises(FrameworkException):
        locator_parser.parse(raw)


def test_value_may_contain_equals_sign():
    by, value = locator_parser.parse("xpath=//*[@text='a=b']")
    assert by == AppiumBy.XPATH
    assert "a=b" in value


def test_text_strategy_builds_ui_selector():
    by, value = locator_parser.parse("text=Welcome")
    assert by == AppiumBy.ANDROID_UIAUTOMATOR
    assert value == 'new UiSelector().text("Welcome")'


def test_escapes_quotes_and_backslashes_for_ui_selector():
    assert locator_parser.escape_ui_selector('say "hi"\\') == 'say \\"hi\\"\\\\'
