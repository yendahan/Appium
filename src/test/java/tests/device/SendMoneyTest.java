package tests.device;

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
 */
@Test(groups = "device")
public class SendMoneyTest extends BaseTest {

    private static final Duration LOGIN_TIMEOUT = Duration.ofSeconds(20);
    private static final Duration REVIEW_TIMEOUT = Duration.ofSeconds(20);

    private static final Duration COMPLETE_TIMEOUT = Duration.ofSeconds(30);

    private static final TestDataLoader DATA = TestDataLoader.forCurrentEnv();
    private SendMoneyPage sendMoney;

    @BeforeMethod(dependsOnMethods = "startSession")
    public void loginAndOpenSendMoney() {
        LoginPage login = new PrivacyNoticePage(driver()).acceptAndContinue().goToLogin();
        JsonNode creds = DATA.node("credentials");
        login.loginAs(creds.get("username").asText(), creds.get("password").asText());

        BiometricSetupPage biometric = login.expectBiometricSetup();
        assertTrue(biometric.isDisplayed(LOGIN_TIMEOUT), "Biometric setup is offered after first login");
        assertTrue(biometric.skip().isDisplayed(LOGIN_TIMEOUT), "Home screen should show after login");
        sendMoney = new SendMoneyPage(driver()).open();
    }

    @DataProvider(name = "qrCodes")
    public Object[][] qrCodes() {
        JsonNode qr = DATA.node("sendMoney").get("qr");
        return new Object[][]{
                {"QRP2P - Static", qr.get("p2pStatic").asText()},
                {"QRP2P - Dynamic", qr.get("p2pDynamic").asText()},
                {"QRP2M - Static", qr.get("p2mStatic").asText()},
                {"QRP2M - Dynamic", qr.get("p2mDynamic").asText()},
        };
    }

    @Test(dataProvider = "qrCodes", description = "Positive: Via QR accepts a valid QR code")
    public void viaQrValid(String type, String resource) {
        sendMoney.viaQr(resourceFile(resource), DATA.node("sendMoney").get("amount").asText());
        assertTrue(sendMoney.isReviewDisplayed(REVIEW_TIMEOUT), type + " should reach the review step");
        completeTransaction("viaQr-" + type);
    }

    @Test(description = "Positive: To Bayad Wallet accepts a valid registered number")
    public void toBayadWalletValid() {
        sendMoney.toBayadWallet(DATA.node("sendMoney").get("bayadWalletNumber").asText(),
                DATA.node("sendMoney").get("amount").asText());
        assertTrue(sendMoney.isReviewDisplayed(REVIEW_TIMEOUT), "Valid wallet number should reach the review step");
        completeTransaction("toBayadWallet");

    }

    @Test(description = "Positive: To Other Banks and E-Wallets accepts a valid Philippine National Bank account")
    public void toOtherBankValid() {
        JsonNode bank = DATA.node("sendMoney").get("otherBank");
        sendMoney.toOtherBank(bank.get("accountNumber").asText(), bank.get("accountName").asText(),
                bank.get("bankName").asText(), DATA.node("sendMoney").get("amount").asText());
        assertTrue(sendMoney.isReviewDisplayed(REVIEW_TIMEOUT), "Valid bank account should reach the review step");
        completeTransaction("toOtherBank");
    }

    /** Confirms the transfer on the review screen (staging environment: this moves real test money). */
    private void completeTransaction(String receiptName) {
        sendMoney.confirm();
        boolean sent = sendMoney.isReceiptDisplayed(COMPLETE_TIMEOUT);
        // Taken before the assertion so the receipt (or whatever the app shows instead) is kept either way.
        sendMoney.actions().screenshot("RECEIPT", receiptName);
        assertTrue(sent, "Receipt should show 'Successfully Sent!' after CONFIRM");
    }

    private static File resourceFile(String resource) {
        URL url = Thread.currentThread().getContextClassLoader().getResource(resource);
        if (url == null) {
            throw new FrameworkException("QR image '" + resource + "' not found on classpath");
        }
        try {
            return new File(url.toURI());
        } catch (URISyntaxException e) {
            throw new FrameworkException("Bad QR image path " + url, e);
        }
    }
}
