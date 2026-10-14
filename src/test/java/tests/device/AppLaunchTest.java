package tests.device;

import base.BaseTest;
import org.testng.annotations.Test;
import pages.LandingPage;

import java.time.Duration;

import static org.testng.Assert.assertTrue;

/** Needs a running Appium server, a connected device/emulator and app + locator config (see README). */
@Test(groups = "device")
public class AppLaunchTest extends BaseTest {

    @Test(description = "Positive: app launches and the configured landing element is visible")
    public void appLaunchesAndLandingElementIsVisible() {
        LandingPage landing = new LandingPage(driver());
        assertTrue(landing.isDisplayed(), "Landing element (app.landing.locator) should be visible after launch");
    }

    @Test(description = "Negative: a non-existent element is reported as not visible, not as an error")
    public void missingElementIsNotVisible() {
        LandingPage landing = new LandingPage(driver());
        assertTrue(landing.isDisplayed(), "precondition: app is on the landing screen");
        assertTrue(!landing.actions().isVisible("id=qa.automation:id/does_not_exist"));
    }

    @Test(description = "Boundary: a 1s wait on a missing element returns promptly (no hang)")
    public void shortWaitTimesOutQuickly() {
        LandingPage landing = new LandingPage(driver());
        long start = System.nanoTime();
        boolean visible = landing.actions().isVisible(
                io.appium.java_client.AppiumBy.id("qa.automation:id/does_not_exist"), Duration.ofSeconds(1));
        long elapsedSeconds = Duration.ofNanos(System.nanoTime() - start).toSeconds();
        assertTrue(!visible);
        assertTrue(elapsedSeconds < 10, "waited " + elapsedSeconds + "s for a 1s timeout");
    }

    @Test(description = "Edge: scrolling to text that does not exist stops after the bound and returns false")
    public void scrollToMissingTextReturnsFalse() {
        LandingPage landing = new LandingPage(driver());
        assertTrue(landing.isDisplayed(), "precondition: app is on the landing screen");
        assertTrue(!landing.actions().scrollToText("\"qa-automation-missing-text\"", 2));
    }
}
