package pages;

import io.appium.java_client.AppiumBy;
import io.appium.java_client.android.AndroidDriver;
import org.openqa.selenium.By;

import java.time.Duration;

/** Login form. The mobile field accepts at most 10 characters (the number without the leading 0). */
public class LoginPage extends BasePage {

    public static final String INVALID_CREDENTIALS_MESSAGE = "Incorrect username or password.";

    private static final By TITLE = AppiumBy.accessibilityId("Log in to your account");
    private static final By MOBILE = AppiumBy.xpath("//android.widget.EditText[@hint='Mobile No.']");
    private static final By PASSWORD = AppiumBy.xpath("//android.widget.EditText[@hint='Password']");
    private static final By LOG_IN_BUTTON = AppiumBy.accessibilityId("LOG IN");
    private static final By ERROR_MESSAGE = AppiumBy.accessibilityId(INVALID_CREDENTIALS_MESSAGE);
    private static final By TRY_AGAIN = AppiumBy.accessibilityId("TRY AGAIN");

    public LoginPage(AndroidDriver driver) {
        super(driver);
    }

    public boolean isDisplayed() {
        return actions.isVisible(TITLE);
    }

    public LoginPage enterMobile(String mobile) {
        actions.type(MOBILE, mobile);
        return this;
    }

    public LoginPage enterPassword(String password) {
        actions.type(PASSWORD, password);
        return this;
    }

    /** The LOG IN button is disabled until both fields hold input. */
    public boolean isSubmitEnabled() {
        return actions.isEnabled(LOG_IN_BUTTON);
    }

    public void submit() {
        actions.tap(LOG_IN_BUTTON);
    }

    /** Fills the form and submits; the caller decides which page to expect next. */
    public void loginAs(String mobile, String password) {
        enterMobile(mobile).enterPassword(password).submit();
    }

    public String mobileFieldText() {
        return actions.text(MOBILE);
    }

    public boolean isInvalidCredentialsErrorShown(Duration timeout) {
        return actions.isVisible(ERROR_MESSAGE, timeout);
    }

    public LoginPage dismissError() {
        actions.tap(TRY_AGAIN);
        return this;
    }

    public BiometricSetupPage expectBiometricSetup() {
        return new BiometricSetupPage(driver);
    }
}
