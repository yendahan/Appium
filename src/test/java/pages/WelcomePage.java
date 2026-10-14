package pages;

import io.appium.java_client.AppiumBy;
import io.appium.java_client.android.AndroidDriver;
import org.openqa.selenium.By;

/** "Let's Get Started" screen with sign-up and the "Log in" link. */
public class WelcomePage extends BasePage {

    private static final By SIGN_UP_BUTTON = AppiumBy.accessibilityId("SIGN UP!");
    private static final By LOG_IN_LINK = AppiumBy.accessibilityId("Log in");

    public WelcomePage(AndroidDriver driver) {
        super(driver);
    }

    public boolean isDisplayed() {
        return actions.isVisible(SIGN_UP_BUTTON);
    }

    public LoginPage goToLogin() {
        actions.tap(LOG_IN_LINK);
        return new LoginPage(driver);
    }
}
