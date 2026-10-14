package pages;

import io.appium.java_client.AppiumBy;
import io.appium.java_client.android.AndroidDriver;
import org.openqa.selenium.By;

import java.time.Duration;

/** Offered once after a successful login on a fresh install. */
public class BiometricSetupPage extends BasePage {

    private static final By TITLE = AppiumBy.accessibilityId("Biometric Setup");
    private static final By SKIP = AppiumBy.accessibilityId("Maybe next time");

    public BiometricSetupPage(AndroidDriver driver) {
        super(driver);
    }

    public boolean isDisplayed(Duration timeout) {
        return actions.isVisible(TITLE, timeout);
    }

    public HomePage skip() {
        actions.tap(SKIP);
        return new HomePage(driver);
    }
}
