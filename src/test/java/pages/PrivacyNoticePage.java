package pages;

import io.appium.java_client.AppiumBy;
import io.appium.java_client.android.AndroidDriver;
import org.openqa.selenium.By;

/** First screen of a fresh install. */
public class PrivacyNoticePage extends BasePage {

    private static final By TITLE = AppiumBy.accessibilityId("Privacy Notice");
    private static final By AGREE = AppiumBy.accessibilityId("AGREE & CONTINUE");

    public PrivacyNoticePage(AndroidDriver driver) {
        super(driver);
    }

    public boolean isDisplayed() {
        return actions.isVisible(TITLE);
    }

    public WelcomePage acceptAndContinue() {
        actions.tap(AGREE);
        return new WelcomePage(driver);
    }
}
