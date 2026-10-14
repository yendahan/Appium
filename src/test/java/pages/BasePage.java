package pages;

import actions.MobileActions;
import io.appium.java_client.android.AndroidDriver;

/** Base for all page objects: owns the driver and the shared actions. */
public abstract class BasePage {

    protected final AndroidDriver driver;
    protected final MobileActions actions;

    protected BasePage(AndroidDriver driver) {
        this.driver = driver;
        this.actions = new MobileActions(driver);
    }

    public MobileActions actions() {
        return actions;
    }
}
