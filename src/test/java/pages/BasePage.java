package pages;

import actions.MobileActions;
import io.appium.java_client.android.AndroidDriver;

/**
 * Base for all page objects: owns the driver and the shared actions.
 * Subclasses hold locators and delegate every interaction to {@link MobileActions}.
 */
public abstract class BasePage {

    // Raw driver, kept only so subclasses can create the next page object or press system Back.
    protected final AndroidDriver driver;
    // Single gateway for waits, taps and typing, so pages never touch the driver for interactions.
    protected final MobileActions actions;

    /**
     * Binds the page to a driver and builds its shared actions helper.
     *
     * @param driver the active Android driver session
     */
    protected BasePage(AndroidDriver driver) {
        // Store the session so subclasses can hand it to the next page they return.
        this.driver = driver;
        // Wrap the same driver so all pages share one consistent wait/tap behaviour.
        this.actions = new MobileActions(driver);
    }

    /**
     * Exposes the actions helper, e.g. for tests that need a screenshot or a raw wait.
     *
     * @return the {@link MobileActions} bound to this page's driver
     */
    public MobileActions actions() {
        return actions;
    }
}
