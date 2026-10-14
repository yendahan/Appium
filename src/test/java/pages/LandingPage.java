package pages;

import config.ConfigManager;
import io.appium.java_client.android.AndroidDriver;
import org.openqa.selenium.By;
import utils.LocatorParser;

import java.time.Duration;

/**
 * First screen shown after launch. Its identifying element is supplied by config key
 * {@code app.landing.locator} (format: strategy=value) because the target app's locators are not known here.
 */
public class LandingPage extends BasePage {

    private final By landingElement;

    public LandingPage(AndroidDriver driver) {
        super(driver);
        this.landingElement = LocatorParser.parse(ConfigManager.get().require("app.landing.locator"));
    }

    public boolean isDisplayed() {
        return actions.isVisible(landingElement);
    }

    public boolean isDisplayedWithin(Duration timeout) {
        return actions.isVisible(landingElement, timeout);
    }
}
