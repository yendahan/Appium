package pages;

import io.appium.java_client.AppiumBy;
import io.appium.java_client.android.AndroidDriver;
import org.openqa.selenium.By;

/** "Let's Get Started" screen with sign-up and the "Log in" link. */
public class WelcomePage extends BasePage {

    // Primary button; used as the marker that this screen is showing.
    private static final By SIGN_UP_BUTTON = AppiumBy.accessibilityId("SIGN UP!");
    // Entry point to the existing-user login flow.
    private static final By LOG_IN_LINK = AppiumBy.accessibilityId("Log in");

    /**
     * Creates the page object; does not interact with the app.
     *
     * @param driver the active Android driver session
     */
    public WelcomePage(AndroidDriver driver) {
        super(driver);
    }

    /**
     * Checks whether the welcome screen is showing.
     *
     * @return true if the SIGN UP! button is visible
     */
    public boolean isDisplayed() {
        // The sign-up button is unique to this screen, so it serves as the identity check.
        return actions.isVisible(SIGN_UP_BUTTON);
    }

    /**
     * Taps the "Log in" link to open the login form.
     * Side effect: navigates away from the welcome screen.
     *
     * @return the {@link LoginPage} now expected on screen
     */
    public LoginPage goToLogin() {
        // Navigate to the login form.
        actions.tap(LOG_IN_LINK);
        // Hand back the next page object so tests can chain calls.
        return new LoginPage(driver);
    }
}
