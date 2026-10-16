package tests.device;

import base.BaseTest;
import org.testng.annotations.Test;
import pages.LandingPage;

import java.time.Duration;

import static org.testng.Assert.assertTrue;

/**
 * Smoke tests for app launch and the basic visibility/wait/scroll helpers in MobileActions.
 * Needs a running Appium server, a connected device/emulator and app + locator config (see README).
 * Side effects: starts a real Appium session per test (via BaseTest); no data is changed in the app.
 */
// Class-level @Test puts every public method in the "device" group, so it only runs with -Dgroups=device.
@Test(groups = "device")
public class AppLaunchTest extends BaseTest {

    /**
     * Scenario: after a fresh launch the configured landing element is on screen.
     * Assertion: LandingPage.isDisplayed() returns true.
     * Side effects: none beyond the session started by BaseTest.
     */
    // Positive case; description shows up in the TestNG report.
    @Test(description = "Positive: app launches and the configured landing element is visible")
    public void appLaunchesAndLandingElementIsVisible() {
        // Build the landing page object on the live driver.
        LandingPage landing = new LandingPage(driver());
        // Fail fast if the app did not reach the landing screen.
        assertTrue(landing.isDisplayed(), "Landing element (app.landing.locator) should be visible after launch");
    }

    /**
     * Scenario: asking for an element that does not exist must yield "not visible" rather than throw.
     * Assertion: isVisible on a bogus resource id returns false.
     * Side effects: none (read-only lookup).
     */
    // Negative case: missing element is a normal false result.
    @Test(description = "Negative: a non-existent element is reported as not visible, not as an error")
    public void missingElementIsNotVisible() {
        // Build the landing page object on the live driver.
        LandingPage landing = new LandingPage(driver());
        // Make sure the app is on a known screen so a false result means "element absent", not "app broken".
        assertTrue(landing.isDisplayed(), "precondition: app is on the landing screen");
        // A made-up id must be reported as not visible instead of raising an exception.
        assertTrue(!landing.actions().isVisible("id=qa.automation:id/does_not_exist"));
    }

    /**
     * Scenario: a 1 second explicit wait on a missing element must time out promptly.
     * Assertion: result is false and elapsed time stays under 10 seconds (generous margin for driver latency).
     * Side effects: none (read-only lookup).
     */
    // Boundary case on the smallest practical timeout.
    @Test(description = "Boundary: a 1s wait on a missing element returns promptly (no hang)")
    public void shortWaitTimesOutQuickly() {
        // Build the landing page object on the live driver.
        LandingPage landing = new LandingPage(driver());
        // Record the start time to measure how long the wait really takes.
        long start = System.nanoTime();
        // Wait at most 1s for an element that is not there; expect false after the timeout.
        boolean visible = landing.actions().isVisible(
                io.appium.java_client.AppiumBy.id("qa.automation:id/does_not_exist"), Duration.ofSeconds(1));
        // Convert elapsed nanoseconds to whole seconds for the comparison.
        long elapsedSeconds = Duration.ofNanos(System.nanoTime() - start).toSeconds();
        // The missing element must not be reported as visible.
        assertTrue(!visible);
        // Guards against the wait ignoring its timeout and hanging.
        assertTrue(elapsedSeconds < 10, "waited " + elapsedSeconds + "s for a 1s timeout");
    }

    /**
     * Scenario: scrolling toward text that is not on the page must stop after the attempt limit.
     * Assertion: scrollToText returns false after at most 2 attempts.
     * Side effects: performs swipe gestures on the device, which may move the visible screen content.
     */
    // Edge case: bounded scrolling must not loop forever.
    @Test(description = "Edge: scrolling to text that does not exist stops after the bound and returns false")
    public void scrollToMissingTextReturnsFalse() {
        // Build the landing page object on the live driver.
        LandingPage landing = new LandingPage(driver());
        // Make sure the app is on a known screen before swiping.
        assertTrue(landing.isDisplayed(), "precondition: app is on the landing screen");
        // Max 2 swipe attempts; unmatched text must return false rather than throw or loop.
        assertTrue(!landing.actions().scrollToText("\"qa-automation-missing-text\"", 2));
    }
}
