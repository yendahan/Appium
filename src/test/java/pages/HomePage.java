package pages;

import io.appium.java_client.AppiumBy;
import io.appium.java_client.android.AndroidDriver;
import org.openqa.selenium.By;

import java.time.Duration;

/** Post-login dashboard. Identified by the "Services" section (the greeting contains the user's name). */
public class HomePage extends BasePage {

    private static final By SERVICES = AppiumBy.accessibilityId("Services");

    public HomePage(AndroidDriver driver) {
        super(driver);
    }

    public boolean isDisplayed() {
        return actions.isVisible(SERVICES);
    }

    public boolean isDisplayed(Duration timeout) {
        return actions.isVisible(SERVICES, timeout);
    }
}
