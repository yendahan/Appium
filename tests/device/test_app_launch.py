import time

import pytest
from appium.webdriver.common.appiumby import AppiumBy

from pages.landing_page import LandingPage

pytestmark = pytest.mark.device


@pytest.mark.zephyr("AMW-T1130")
def test_app_launches_and_landing_element_is_visible(driver):
    """Positive: app launches and the configured landing element is visible."""
    assert LandingPage(driver).is_displayed(), "Landing element (app.landing.locator) should be visible after launch"


@pytest.mark.zephyr("AMW-T1131")
def test_missing_element_is_not_visible(driver):
    """Negative: a non-existent element is reported as not visible, not as an error."""
    landing = LandingPage(driver)
    assert landing.is_displayed(), "precondition: app is on the landing screen"
    assert not landing.actions.is_visible("id=qa.automation:id/does_not_exist")


@pytest.mark.zephyr("AMW-T1132")
def test_short_wait_times_out_quickly(driver):
    """Boundary: a 1s wait on a missing element returns promptly (no hang)."""
    landing = LandingPage(driver)
    start = time.monotonic()
    visible = landing.actions.is_visible((AppiumBy.ID, "qa.automation:id/does_not_exist"), 1)
    elapsed = time.monotonic() - start
    assert not visible
    assert elapsed < 10, f"waited {elapsed:.0f}s for a 1s timeout"


@pytest.mark.zephyr("AMW-T1133")
def test_scroll_to_missing_text_returns_false(driver):
    """Edge: scrolling to text that does not exist stops after the bound and returns false."""
    landing = LandingPage(driver)
    assert landing.is_displayed(), "precondition: app is on the landing screen"
    assert not landing.actions.scroll_to_text('"qa-automation-missing-text"', 2)
