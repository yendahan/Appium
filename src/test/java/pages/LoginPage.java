package pages;

import io.appium.java_client.AppiumBy;
import io.appium.java_client.android.AndroidDriver;
import org.openqa.selenium.By;

import java.time.Duration;

/** Login form. The mobile field accepts at most 10 characters (the number without the leading 0). */
public class LoginPage extends BasePage {

    /** Text the app shows for a failed login; shared with tests and used as the error locator below. */
    public static final String INVALID_CREDENTIALS_MESSAGE = "Incorrect username or password.";

    // Form heading; confirms the login screen is showing.
    private static final By TITLE = AppiumBy.accessibilityId("Log in to your account");
    // Located by hint because the field has no accessibility id.
    private static final By MOBILE = AppiumBy.xpath("//android.widget.EditText[@hint='Mobile No.']");
    // Located by hint because the field has no accessibility id.
    private static final By PASSWORD = AppiumBy.xpath("//android.widget.EditText[@hint='Password']");
    // Submit button; disabled until both fields have input.
    private static final By LOG_IN_BUTTON = AppiumBy.accessibilityId("LOG IN");
    // The error is exposed as content-desc equal to its message text.
    private static final By ERROR_MESSAGE = AppiumBy.accessibilityId(INVALID_CREDENTIALS_MESSAGE);
    // Button on the error dialog that returns to the form.
    private static final By TRY_AGAIN = AppiumBy.accessibilityId("TRY AGAIN");

    /**
     * Creates the page object; does not interact with the app.
     *
     * @param driver the active Android driver session
     */
    public LoginPage(AndroidDriver driver) {
        super(driver);
    }

    /**
     * Checks whether the login form is showing.
     *
     * @return true if the form heading is visible
     */
    public boolean isDisplayed() {
        // Heading is the identity marker for this screen.
        return actions.isVisible(TITLE);
    }

    /**
     * Types the mobile number into the form.
     * Side effect: changes the field's content.
     *
     * @param mobile number without the leading 0 (the field caps at 10 characters)
     * @return this page, for chaining
     */
    public LoginPage enterMobile(String mobile) {
        // Type into the mobile field.
        actions.type(MOBILE, mobile);
        return this;
    }

    /**
     * Types the password into the form. Callers must source it from env vars, never hard-code it.
     * Side effect: changes the field's content.
     *
     * @param password the password to enter
     * @return this page, for chaining
     */
    public LoginPage enterPassword(String password) {
        // Type into the password field.
        actions.type(PASSWORD, password);
        return this;
    }

    /**
     * Reports whether LOG IN can be tapped; the button is disabled until both fields hold input.
     *
     * @return true if the LOG IN button is enabled
     */
    public boolean isSubmitEnabled() {
        // Enabled state reflects whether the form considers itself filled in.
        return actions.isEnabled(LOG_IN_BUTTON);
    }

    /**
     * Taps LOG IN.
     * Side effect: sends a login request; repeated wrong attempts can lock the account.
     */
    public void submit() {
        // Submit the form.
        actions.tap(LOG_IN_BUTTON);
    }

    /**
     * Fills the form and submits; the caller decides which page to expect next.
     * Side effect: sends a login request; repeated wrong attempts can lock the account.
     *
     * @param mobile   number without the leading 0
     * @param password the account password
     */
    public void loginAs(String mobile, String password) {
        // Fluent chain: fill both fields, then submit.
        enterMobile(mobile).enterPassword(password).submit();
    }

    /**
     * Reads the current content of the mobile field, e.g. to verify the 10-character cap.
     *
     * @return the text currently in the mobile field
     */
    public String mobileFieldText() {
        // Read back what the app actually accepted, not what was typed.
        return actions.text(MOBILE);
    }

    /**
     * Waits for the "Incorrect username or password." error.
     *
     * @param timeout maximum time to wait for the error
     * @return true if the error appeared before the timeout
     */
    public boolean isInvalidCredentialsErrorShown(Duration timeout) {
        // Timed check because the error arrives after a network round trip.
        return actions.isVisible(ERROR_MESSAGE, timeout);
    }

    /**
     * Dismisses the error dialog via TRY AGAIN.
     * Side effect: closes the dialog and returns to the form.
     *
     * @return this page, for chaining
     */
    public LoginPage dismissError() {
        // Close the dialog so the form can be edited again.
        actions.tap(TRY_AGAIN);
        return this;
    }

    /**
     * Declares that a successful login should land on biometric setup; does not interact with the app.
     *
     * @return the {@link BiometricSetupPage} expected next
     */
    public BiometricSetupPage expectBiometricSetup() {
        // Only builds the next page object; callers verify it with isDisplayed(timeout).
        return new BiometricSetupPage(driver);
    }
}
