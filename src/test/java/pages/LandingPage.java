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

    // Config-driven locator; resolved at construction so a missing key fails fast.
    private final By landingElement;

    /**
     * Creates the page and resolves its locator from configuration.
     *
     * @param driver the active Android driver session
     * @throws RuntimeException if {@code app.landing.locator} is missing or malformed (from config/parser)
     */
    public LandingPage(AndroidDriver driver) {
        super(driver);
        // Parse "strategy=value" into a By; require() throws if the key is absent, surfacing bad setup early.
        this.landingElement = LocatorParser.parse(ConfigManager.get().require("app.landing.locator"));
    }

    /**
     * Checks whether the landing element is visible right now, using the default wait.
     *
     * @return true if the landing element is visible
     */
    public boolean isDisplayed() {
        // Default-timeout visibility check; no screen change.
        return actions.isVisible(landingElement);
    }

    /**
     * Checks whether the landing element becomes visible within a custom timeout.
     *
     * @param timeout maximum time to wait for the element
     * @return true if the element appeared before the timeout
     */
    public boolean isDisplayedWithin(Duration timeout) {
        // Explicit timeout lets slow cold starts wait longer without changing the default.
        return actions.isVisible(landingElement, timeout);
    }
}
