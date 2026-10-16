package pages;

import io.appium.java_client.AppiumBy;
import io.appium.java_client.android.AndroidDriver;
import org.openqa.selenium.By;

/** First screen of a fresh install. */
public class PrivacyNoticePage extends BasePage {

    // Screen heading; used to confirm the notice is showing.
    private static final By TITLE = AppiumBy.accessibilityId("Privacy Notice");
    // Consent button that moves on to the welcome screen.
    private static final By AGREE = AppiumBy.accessibilityId("AGREE & CONTINUE");

    /**
     * Creates the page object; does not interact with the app.
     *
     * @param driver the active Android driver session
     */
    public PrivacyNoticePage(AndroidDriver driver) {
        super(driver);
    }

    /**
     * Checks whether the privacy notice is showing.
     *
     * @return true if the "Privacy Notice" title is visible
     */
    public boolean isDisplayed() {
        // Title is the identity marker for this screen.
        return actions.isVisible(TITLE);
    }

    /**
     * Accepts the privacy notice.
     * Side effect: records consent in the app and navigates to the welcome screen.
     *
     * @return the {@link WelcomePage} now expected on screen
     */
    public WelcomePage acceptAndContinue() {
        // Consent is required before the app lets the user proceed.
        actions.tap(AGREE);
        // Hand back the next page object so tests can chain calls.
        return new WelcomePage(driver);
    }
}
