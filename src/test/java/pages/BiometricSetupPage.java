package pages;

import io.appium.java_client.AppiumBy;
import io.appium.java_client.android.AndroidDriver;
import org.openqa.selenium.By;

import java.time.Duration;

/** Offered once after a successful login on a fresh install. */
public class BiometricSetupPage extends BasePage {

    // Prompt heading; confirms the biometric offer is showing.
    private static final By TITLE = AppiumBy.accessibilityId("Biometric Setup");
    // Decline option, so tests avoid enrolling biometrics on the emulator.
    private static final By SKIP = AppiumBy.accessibilityId("Maybe next time");

    /**
     * Creates the page object; does not interact with the app.
     *
     * @param driver the active Android driver session
     */
    public BiometricSetupPage(AndroidDriver driver) {
        super(driver);
    }

    /**
     * Waits for the biometric prompt, which only appears on a fresh install after login.
     *
     * @param timeout maximum time to wait for the prompt
     * @return true if the prompt appeared before the timeout
     */
    public boolean isDisplayed(Duration timeout) {
        // Timed check because the prompt may be absent; callers use the result to decide whether to skip.
        return actions.isVisible(TITLE, timeout);
    }

    /**
     * Declines biometric setup.
     * Side effect: dismisses the prompt and navigates to the home screen.
     *
     * @return the {@link HomePage} now expected on screen
     */
    public HomePage skip() {
        // Decline so the flow continues to the dashboard.
        actions.tap(SKIP);
        // Hand back the next page object so tests can chain calls.
        return new HomePage(driver);
    }
}
