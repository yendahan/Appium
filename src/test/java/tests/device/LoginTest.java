package tests.device;

import base.BaseTest;
import com.fasterxml.jackson.databind.JsonNode;
import data.TestDataLoader;
import org.testng.annotations.BeforeMethod;
import org.testng.annotations.Test;
import pages.BiometricSetupPage;
import pages.HomePage;
import pages.LoginPage;
import pages.PrivacyNoticePage;

import java.time.Duration;

import static org.testng.Assert.assertEquals;
import static org.testng.Assert.assertFalse;
import static org.testng.Assert.assertTrue;

/**
 * Accept the privacy notice, open the login form and sign in.
 * Valid credentials come from env vars TEST_USERNAME / TEST_PASSWORD (see README); nothing is stored in the repo.
 * Side effects: the negative tests submit wrong passwords, which can lock the test account temporarily.
 */
// Class-level @Test puts every public method in the "device" group, so it only runs with -Dgroups=device.
@Test(groups = "device")
public class LoginTest extends BaseTest {

    // Max wait for the post-login screens after a successful sign-in.
    private static final Duration LOGIN_TIMEOUT = Duration.ofSeconds(20);
    // Max wait for the invalid-credentials error dialog to appear.
    private static final Duration ERROR_TIMEOUT = Duration.ofSeconds(15);
    // Short wait used to prove something does NOT appear (keeps negative tests fast).
    private static final Duration NEGATIVE_TIMEOUT = Duration.ofSeconds(3);

    // Test data for the current env; credential placeholders resolve from env vars when the node is read.
    private final TestDataLoader data = TestDataLoader.forCurrentEnv();
    // Login form page object, rebuilt before every test by openLoginForm().
    private LoginPage loginPage;

    /**
     * Precondition for every test: from a fresh session, accept the privacy notice and open the login form.
     * Side effects: navigates the app; leaves loginPage set for the test body.
     */
    // Runs after BaseTest.startSession so the driver exists before navigation begins.
    @BeforeMethod(dependsOnMethods = "startSession")
    public void openLoginForm() {
        // Privacy notice is the first screen of a fresh session.
        PrivacyNoticePage notice = new PrivacyNoticePage(driver());
        // Confirm we really are on the first screen before navigating.
        assertTrue(notice.isDisplayed(), "Privacy notice should be the first screen of a fresh session");
        // Accept the notice and move to the login form; keep the page object for the tests.
        loginPage = notice.acceptAndContinue().goToLogin();
        // Stop early if the form did not open, so tests do not fail with misleading errors.
        assertTrue(loginPage.isDisplayed(), "Login form should be displayed");
    }

    /**
     * Scenario: sign in with the valid account from environment variables.
     * Assertion: biometric setup is offered, and skipping it lands on the home screen.
     * Side effects: creates a logged-in session on staging.
     */
    // Positive case.
    @Test(description = "Positive: valid credentials reach the home screen")
    public void validCredentialsReachHome() {
        // Read the credentials node (values resolved from TEST_USERNAME / TEST_PASSWORD).
        JsonNode creds = data.node("credentials");
        // Submit the login form with the valid account.
        loginPage.loginAs(creds.get("username").asText(), creds.get("password").asText());

        // First login prompts for biometrics; move to that page object.
        BiometricSetupPage biometric = loginPage.expectBiometricSetup();
        // Biometric prompt proves the credentials were accepted.
        assertTrue(biometric.isDisplayed(LOGIN_TIMEOUT), "Biometric setup is offered after first login");
        // Skipping biometrics should end on the home screen.
        assertTrue(biometric.skip().isDisplayed(LOGIN_TIMEOUT), "Home screen should show after skipping biometrics");
    }

    /**
     * Scenario: sign in with an account that does not exist.
     * Assertion: the invalid-credentials error shows, TRY AGAIN returns to the form, home is never reached.
     * Side effects: failed login attempt on staging.
     */
    // Negative case.
    @Test(description = "Negative: unknown account is rejected with an error and can be retried")
    public void unknownAccountIsRejected() {
        // Read the deliberately invalid account from test data.
        JsonNode bad = data.node("invalidLogin");
        // Submit the invalid account.
        loginPage.loginAs(bad.get("username").asText(), bad.get("password").asText());

        // The app must show the invalid-credentials message.
        assertTrue(loginPage.isInvalidCredentialsErrorShown(ERROR_TIMEOUT),
                "Expected '" + LoginPage.INVALID_CREDENTIALS_MESSAGE + "'");
        // Dismissing the error must bring the form back so the user can retry.
        assertTrue(loginPage.dismissError().isDisplayed(), "TRY AGAIN should return to the login form");
        // Home must stay unreachable after a failed login.
        assertFalse(new HomePage(driver()).isDisplayed(NEGATIVE_TIMEOUT), "Must not reach home");
    }

    /**
     * Scenario: valid username combined with a wrong password.
     * Assertion: the error is shown and home is not reached.
     * Side effects: counts as a failed attempt on the real account and may lock it ("blocked temporarily").
     */
    // Negative case.
    @Test(description = "Negative: valid username with a wrong password never reaches home")
    public void wrongPasswordIsRejected() {
        // Read the valid account (only the username is used).
        JsonNode creds = data.node("credentials");
        // Pair the real username with the known-bad password.
        loginPage.loginAs(creds.get("username").asText(), data.node("invalidLogin").get("password").asText());

        // The app must reject the attempt with the error message.
        assertTrue(loginPage.isInvalidCredentialsErrorShown(ERROR_TIMEOUT));
        // Home must stay unreachable.
        assertFalse(new HomePage(driver()).isDisplayed(NEGATIVE_TIMEOUT));
    }

    /**
     * Scenario: LOG IN button state for an empty and a half-filled form.
     * Assertion: the button is disabled in both cases and home is not reached.
     * Side effects: types a mobile number into the field; nothing is submitted.
     */
    // Edge case.
    @Test(description = "Edge: LOG IN stays disabled for an empty form and for a half-filled form")
    public void submitIsDisabledUntilBothFieldsAreFilled() {
        // Nothing entered yet, so submit must be disabled.
        assertFalse(loginPage.isSubmitEnabled(), "Empty form must not be submittable");

        // Fill only the mobile field, leaving the password empty.
        loginPage.enterMobile(data.node("invalidLogin").get("username").asText());
        // One field filled is still not enough to submit.
        assertFalse(loginPage.isSubmitEnabled(), "Mobile only must not be submittable");
        // Confirm the app did not move past the login form.
        assertFalse(new HomePage(driver()).isDisplayed(NEGATIVE_TIMEOUT));
    }

    /**
     * Scenario: type 11 digits into the mobile field.
     * Assertion: only the first 10 characters are kept.
     * Side effects: types into the field; nothing is submitted.
     */
    // Boundary case on the field's max length.
    @Test(description = "Boundary: the mobile field keeps at most 10 characters")
    public void mobileFieldIsLimitedToTenCharacters() {
        // Take the over-long (11 digit) value from test data.
        String elevenDigits = data.node("boundary").get("elevenDigitMobile").asText();
        // Type it into the mobile field.
        loginPage.enterMobile(elevenDigits);

        // The field must have truncated the input to its first 10 characters.
        assertEquals(loginPage.mobileFieldText(), elevenDigits.substring(0, 10));
    }
}
