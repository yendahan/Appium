package pages;

import io.appium.java_client.AppiumBy;
import io.appium.java_client.android.AndroidDriver;
import org.openqa.selenium.By;

import java.time.Duration;

/** Post-login dashboard. Identified by the "Services" section (the greeting contains the user's name). */
public class HomePage extends BasePage {

    // Stable marker for the dashboard; the greeting text varies per user so it cannot be used.
    private static final By SERVICES = AppiumBy.accessibilityId("Services");

    /**
     * Creates the page object; does not interact with the app.
     *
     * @param driver the active Android driver session
     */
    public HomePage(AndroidDriver driver) {
        super(driver);
    }

    /**
     * Checks whether the home dashboard is showing, using the default wait.
     *
     * @return true if the Services section is visible
     */
    public boolean isDisplayed() {
        // Services section is the identity marker for the dashboard.
        return actions.isVisible(SERVICES);
    }

    /**
     * Waits up to a custom timeout for the home dashboard, e.g. right after login.
     *
     * @param timeout maximum time to wait for the Services section
     * @return true if the dashboard appeared before the timeout
     */
    public boolean isDisplayed(Duration timeout) {
        // Longer wait covers the post-login load time.
        return actions.isVisible(SERVICES, timeout);
    }
}
