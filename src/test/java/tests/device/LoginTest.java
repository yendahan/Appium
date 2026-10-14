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
 */
@Test(groups = "device")
public class LoginTest extends BaseTest {

    private static final Duration LOGIN_TIMEOUT = Duration.ofSeconds(20);
    private static final Duration ERROR_TIMEOUT = Duration.ofSeconds(15);
    private static final Duration NEGATIVE_TIMEOUT = Duration.ofSeconds(3);

    private final TestDataLoader data = TestDataLoader.forCurrentEnv();
    private LoginPage loginPage;

    @BeforeMethod(dependsOnMethods = "startSession")
    public void openLoginForm() {
        PrivacyNoticePage notice = new PrivacyNoticePage(driver());
        assertTrue(notice.isDisplayed(), "Privacy notice should be the first screen of a fresh session");
        loginPage = notice.acceptAndContinue().goToLogin();
        assertTrue(loginPage.isDisplayed(), "Login form should be displayed");
    }

    @Test(description = "Positive: valid credentials reach the home screen")
    public void validCredentialsReachHome() {
        JsonNode creds = data.node("credentials");
        loginPage.loginAs(creds.get("username").asText(), creds.get("password").asText());

        BiometricSetupPage biometric = loginPage.expectBiometricSetup();
        assertTrue(biometric.isDisplayed(LOGIN_TIMEOUT), "Biometric setup is offered after first login");
        assertTrue(biometric.skip().isDisplayed(LOGIN_TIMEOUT), "Home screen should show after skipping biometrics");
    }

    @Test(description = "Negative: unknown account is rejected with an error and can be retried")
    public void unknownAccountIsRejected() {
        JsonNode bad = data.node("invalidLogin");
        loginPage.loginAs(bad.get("username").asText(), bad.get("password").asText());

        assertTrue(loginPage.isInvalidCredentialsErrorShown(ERROR_TIMEOUT),
                "Expected '" + LoginPage.INVALID_CREDENTIALS_MESSAGE + "'");
        assertTrue(loginPage.dismissError().isDisplayed(), "TRY AGAIN should return to the login form");
        assertFalse(new HomePage(driver()).isDisplayed(NEGATIVE_TIMEOUT), "Must not reach home");
    }

    @Test(description = "Negative: valid username with a wrong password never reaches home")
    public void wrongPasswordIsRejected() {
        JsonNode creds = data.node("credentials");
        loginPage.loginAs(creds.get("username").asText(), data.node("invalidLogin").get("password").asText());

        assertTrue(loginPage.isInvalidCredentialsErrorShown(ERROR_TIMEOUT));
        assertFalse(new HomePage(driver()).isDisplayed(NEGATIVE_TIMEOUT));
    }

    @Test(description = "Edge: LOG IN stays disabled for an empty form and for a half-filled form")
    public void submitIsDisabledUntilBothFieldsAreFilled() {
        assertFalse(loginPage.isSubmitEnabled(), "Empty form must not be submittable");

        loginPage.enterMobile(data.node("invalidLogin").get("username").asText());
        assertFalse(loginPage.isSubmitEnabled(), "Mobile only must not be submittable");
        assertFalse(new HomePage(driver()).isDisplayed(NEGATIVE_TIMEOUT));
    }

    @Test(description = "Boundary: the mobile field keeps at most 10 characters")
    public void mobileFieldIsLimitedToTenCharacters() {
        String elevenDigits = data.node("boundary").get("elevenDigitMobile").asText();
        loginPage.enterMobile(elevenDigits);

        assertEquals(loginPage.mobileFieldText(), elevenDigits.substring(0, 10));
    }
}
