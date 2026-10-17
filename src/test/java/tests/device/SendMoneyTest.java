package tests.device;

import listeners.ZephyrCase;
import base.BaseTest;
import com.fasterxml.jackson.databind.JsonNode;
import data.TestDataLoader;
import exceptions.FrameworkException;
import org.testng.annotations.BeforeMethod;
import org.testng.annotations.DataProvider;
import org.testng.annotations.Test;
import pages.BiometricSetupPage;
import pages.LoginPage;
import pages.PrivacyNoticePage;
import pages.SendMoneyPage;

import java.io.File;
import java.net.URISyntaxException;
import java.net.URL;
import java.time.Duration;

import static org.testng.Assert.assertTrue;

/**
 * Services &gt; Send Money valid transactions: Via QR (P2P/P2M, static/dynamic), To Bayad Wallet and To Other
 * Banks and E-Wallets. Each test stops at the review step so no real money is moved.
 * Requires TEST_USERNAME / TEST_PASSWORD (see README).
 * Side effects: CAUTION, the tests currently tap CONFIRM via completeTransaction(), which moves real Php 10 on
 * staging per test (six per run). Do not run casually.
 */
// Class-level @Test puts every public method in the "device" group, so it only runs with -Dgroups=device.
@Test(groups = "device")
public class SendMoneyTest extends BaseTest {

    // Max wait for the post-login screens.
    private static final Duration LOGIN_TIMEOUT = Duration.ofSeconds(20);
    // Max wait for the review screen after filling in the transfer details.
    private static final Duration REVIEW_TIMEOUT = Duration.ofSeconds(20);

    // Max wait for the receipt after tapping CONFIRM (the transfer is processed server side).
    private static final Duration COMPLETE_TIMEOUT = Duration.ofSeconds(30);

    // Test data for the current env; credential placeholders resolve from env vars when the node is read.
    private static final TestDataLoader DATA = TestDataLoader.forCurrentEnv();
    // Send Money page object, created fresh before every test by loginAndOpenSendMoney().
    private SendMoneyPage sendMoney;

    /**
     * Precondition for every test: log in with the env-var account, skip biometrics and open Send Money.
     * Side effects: creates a logged-in staging session and navigates to the Send Money screen.
     */
    // Runs after BaseTest.startSession so the driver exists before navigation begins.
    @BeforeMethod(dependsOnMethods = "startSession")
    public void loginAndOpenSendMoney() {
        // Accept the privacy notice and open the login form.
        LoginPage login = new PrivacyNoticePage(driver()).acceptAndContinue().goToLogin();
        // Credentials come from TEST_USERNAME / TEST_PASSWORD, never from the repo.
        JsonNode creds = DATA.node("credentials");
        // Sign in.
        login.loginAs(creds.get("username").asText(), creds.get("password").asText());

        // First login prompts for biometrics.
        BiometricSetupPage biometric = login.expectBiometricSetup();
        // Biometric prompt proves the login succeeded.
        assertTrue(biometric.isDisplayed(LOGIN_TIMEOUT), "Biometric setup is offered after first login");
        // Skipping biometrics should land on home.
        assertTrue(biometric.skip().isDisplayed(LOGIN_TIMEOUT), "Home screen should show after login");
        // Open Services > Send Money for the test body.
        sendMoney = new SendMoneyPage(driver()).open();
    }

    /**
     * Supplies the four QR scenarios to viaQrValid.
     *
     * @return rows of {display label, classpath resource of the QR image} for P2P/P2M, static/dynamic
     */
    // Feeds viaQrValid once per row, so that test runs four times.
    @DataProvider(name = "qrCodes")
    public Object[][] qrCodes() {
        // QR image resource names live under sendMoney.qr in the test data.
        JsonNode qr = DATA.node("sendMoney").get("qr");
        // One row per QR type: label for messages, resource path for the upload.
        return new Object[][]{
                {"QRP2P - Static", qr.get("p2pStatic").asText()},
                {"QRP2P - Dynamic", qr.get("p2pDynamic").asText()},
                {"QRP2M - Static", qr.get("p2mStatic").asText()},
                {"QRP2M - Dynamic", qr.get("p2mDynamic").asText()},
        };
    }

    /**
     * Scenario: send money by scanning/uploading a valid QR code.
     * Assertion: the review step is shown, then the receipt appears after CONFIRM.
     * Side effects: confirms the transfer, moving real test money on staging.
     *
     * @param type     QR type label used in assertion messages and the receipt screenshot name
     * @param resource classpath location of the QR image to upload
     */
    // Positive case, driven by the qrCodes provider.
    @Test(dataProvider = "qrCodes", description = "Positive: Via QR accepts a valid QR code")
    @ZephyrCase("AMW-T1139")
    public void viaQrValid(String type, String resource) {
        // Upload the QR image and enter the configured amount.
        sendMoney.viaQr(resourceFile(resource), DATA.node("sendMoney").get("amount").asText());
        // A valid QR must lead to the review step.
        assertTrue(sendMoney.isReviewDisplayed(REVIEW_TIMEOUT), type + " should reach the review step");
        // Finish the transfer and capture the receipt.
        completeTransaction("viaQr-" + type);
    }

    /**
     * Scenario: send to a valid registered Bayad Wallet number.
     * Assertion: the review step is shown, then the receipt appears after CONFIRM.
     * Side effects: confirms the transfer, moving real test money on staging.
     */
    // Positive case.
    @Test(description = "Positive: To Bayad Wallet accepts a valid registered number")
    @ZephyrCase("AMW-T1140")
    public void toBayadWalletValid() {
        // Enter the wallet number and the configured amount.
        sendMoney.toBayadWallet(DATA.node("sendMoney").get("bayadWalletNumber").asText(),
                DATA.node("sendMoney").get("amount").asText());
        // A valid wallet number must lead to the review step.
        assertTrue(sendMoney.isReviewDisplayed(REVIEW_TIMEOUT), "Valid wallet number should reach the review step");
        // Finish the transfer and capture the receipt.
        completeTransaction("toBayadWallet");

    }

    /**
     * Scenario: send to a valid Philippine National Bank account via Other Banks and E-Wallets.
     * Assertion: the review step is shown, then the receipt appears after CONFIRM.
     * Side effects: confirms the transfer, moving real test money on staging.
     */
    // Positive case.
    @Test(description = "Positive: To Other Banks and E-Wallets accepts a valid Philippine National Bank account")
    @ZephyrCase("AMW-T1141")
    public void toOtherBankValid() {
        // Bank account details come from test data.
        JsonNode bank = DATA.node("sendMoney").get("otherBank");
        // Enter account number, name, bank and the configured amount.
        sendMoney.toOtherBank(bank.get("accountNumber").asText(), bank.get("accountName").asText(),
                bank.get("bankName").asText(), DATA.node("sendMoney").get("amount").asText());
        // A valid account must lead to the review step.
        assertTrue(sendMoney.isReviewDisplayed(REVIEW_TIMEOUT), "Valid bank account should reach the review step");
        // Finish the transfer and capture the receipt.
        completeTransaction("toOtherBank");
    }

    /**
     * Confirms the transfer on the review screen (staging environment: this moves real test money).
     * Always saves a RECEIPT screenshot, then asserts the receipt showed success.
     *
     * @param receiptName name for the receipt screenshot file
     */
    private void completeTransaction(String receiptName) {
        // Tap CONFIRM; this is the step that actually moves the money.
        sendMoney.confirm();
        // Wait for the success receipt and remember the outcome.
        boolean sent = sendMoney.isReceiptDisplayed(COMPLETE_TIMEOUT);
        // Taken before the assertion so the receipt (or whatever the app shows instead) is kept either way.
        sendMoney.actions().screenshot("RECEIPT", receiptName);
        // Fail the test if the receipt did not show success.
        assertTrue(sent, "Receipt should show 'Successfully Sent!' after CONFIRM");
    }

    /**
     * Resolves a classpath resource name to a real file the driver can push to the device.
     *
     * @param resource classpath location of the file, e.g. a QR image under test resources
     * @return the resolved File
     * @throws FrameworkException if the resource is missing or its URL is not a valid file path
     */
    private static File resourceFile(String resource) {
        // Look the resource up through the context classloader, which sees test resources.
        URL url = Thread.currentThread().getContextClassLoader().getResource(resource);
        // A missing image is a setup error; fail with a clear message.
        if (url == null) {
            throw new FrameworkException("QR image '" + resource + "' not found on classpath");
        }
        try {
            // Convert the URL to a File (URI form handles spaces and special characters).
            return new File(url.toURI());
        } catch (URISyntaxException e) {
            // Wrap the checked exception so callers deal with a single framework exception type.
            throw new FrameworkException("Bad QR image path " + url, e);
        }
    }
}
