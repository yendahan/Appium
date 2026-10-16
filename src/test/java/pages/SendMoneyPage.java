package pages;

import io.appium.java_client.AppiumBy;
import io.appium.java_client.android.AndroidDriver;
import org.openqa.selenium.By;

import java.io.File;
import java.time.Duration;
import java.util.Map;

/**
 * Services &gt; Send Money. Locators are accessibility ids taken from the visible labels and have NOT yet been
 * verified against the running app; adjust them here (and only here) if a lookup fails.
 */
public class SendMoneyPage extends BasePage {

    private static final By SERVICES = AppiumBy.accessibilityId("Services");
    private static final By SEND_MONEY = AppiumBy.accessibilityId("Send Money");
    private static final By VIA_QR = AppiumBy.accessibilityId("Via QR");
    private static final By TO_BAYAD_WALLET = AppiumBy.accessibilityId("To Bayad Wallet");
    private static final By TO_OTHER_BANKS = AppiumBy.accessibilityId("To Other Banks and E-Wallets");
    private static final By UPLOAD_QR = AppiumBy.accessibilityId("Upload QR from Gallery");
    private static final By SEND_TO = AppiumBy.xpath("//android.widget.EditText[@hint='Send money to']");
    private static final By AMOUNT = AppiumBy.xpath("//android.widget.EditText[@hint='Enter cash amount']");
    private static final By ACCOUNT_NO = AppiumBy.xpath("//android.widget.EditText[@hint='Account No.']");
    private static final By BANK_AMOUNT = AppiumBy.xpath("//android.widget.EditText[@hint='Amount']");
    private static final By ACCOUNT_NAME = AppiumBy.xpath("//android.widget.EditText[@hint='Account Name']");
    private static final By NEWEST_PHOTO = AppiumBy.androidUIAutomator(
            "new UiSelector().descriptionStartsWith(\"Photo taken\").instance(0)");
    private static final By PICKER_DONE = AppiumBy.xpath("//*[@text='Done' or @content-desc='Done']");
    private static final By AMOUNT_HEADING = AppiumBy.accessibilityId("Enter or Select Amount (Php)");
    private static final By SEARCH_ICON = AppiumBy.xpath("(//android.widget.Button)[2]"); // unlabeled, top right
    private static final By BANK_SEARCH = AppiumBy.className("android.widget.EditText");
    private static final By SUCCESS = AppiumBy.xpath("//*[contains(@content-desc,'Successfully Sent')]");
    private static final By CONFIRM = AppiumBy.accessibilityId("CONFIRM");
    private static final By NEXT = AppiumBy.accessibilityId("NEXT");
    private static final By REVIEW = AppiumBy.xpath(
            "//*[@content-desc='Send Money Confirmation' or @content-desc='Payment Confirmation']");

    private static final int SEARCH_ATTEMPTS = 2;
    private static final int BANK_LIST_ATTEMPTS = 3;
    private static final String GALLERY_DIR = "/sdcard/Pictures/";

    public SendMoneyPage(AndroidDriver driver) {
        super(driver);
    }

    /** From the home screen: Services &gt; Send Money. */
    public SendMoneyPage open() {
        actions.tap(SERVICES);
        actions.tap(SEND_MONEY);
        return this;
    }

    public SendMoneyPage viaQr(File qrImage, String amount) {
        actions.tap(VIA_QR);
        pushToGallery(qrImage);
        actions.tap(UPLOAD_QR);
        // The emulator indexes the pushed file asynchronously: reopen the picker once if it is not listed yet.
        if (!actions.isVisible(NEWEST_PHOTO, Duration.ofSeconds(8))) {
            if (!actions.isVisible(UPLOAD_QR, Duration.ofSeconds(2))) {
                driver.navigate().back(); // picker is open but empty: close it
            }
            if (!actions.isVisible(UPLOAD_QR, Duration.ofSeconds(2))) {
                actions.tap(VIA_QR); // back left the QR screen
            }
            actions.tap(UPLOAD_QR);
        }
        actions.tap(NEWEST_PHOTO); // newest first, and the image pushed above is the newest
        actions.tap(PICKER_DONE);
        // Dynamic QR codes carry their own amount; static ones leave it empty for the sender to fill in.
        String prefilled = actions.text(BANK_AMOUNT);
        if (prefilled.isBlank() || prefilled.equals("Amount")) {
            actions.type(BANK_AMOUNT, amount);
            actions.tap(ACCOUNT_NAME);
        }
        actions.tap(NEXT);
        return this;
    }

    public SendMoneyPage toBayadWallet(String number, String amount) {
        actions.tap(TO_BAYAD_WALLET);
        return fillRecipient(number, amount);
    }

    /** Picks the bank from the "Banks &amp; Wallets" list (each row's description is "&lt;name&gt;\nBank"). */
    public SendMoneyPage toOtherBank(String accountNumber, String accountName, String bankName, String amount) {
        By result = AppiumBy.androidUIAutomator("new UiSelector().descriptionStartsWith(\"" + bankName + "\")");
        // The bank list is loaded from the backend and is sometimes incomplete ("No results found" for a bank that
        // exists), so reopen it from scratch a couple of times before giving up.
        for (int open = 0; open < BANK_LIST_ATTEMPTS && !searchBank(bankName, result); open++) {
            backToMenu();
        }
        actions.waitVisible(result).click(); // list rows are not flagged clickable, so skip the clickable wait
        actions.type(ACCOUNT_NO, accountNumber);
        actions.type(ACCOUNT_NAME, accountName);
        hideKeyboard(); // the keyboard covers the Amount field on this form
        actions.type(BANK_AMOUNT, amount);
        actions.tap(ACCOUNT_NAME); // blur: the amount is only committed when it loses focus (the heading scrolls away)
        actions.tap(NEXT);
        return this;
    }

    /** Back closes the keyboard first, so press it until the Send Money options are showing again. */
    public SendMoneyPage confirm() {
        actions.tap(CONFIRM);
        return this;
    }

    /** True when the receipt ("Successfully Sent!" with the reference number) is shown after CONFIRM. */
    public boolean isReceiptDisplayed(Duration timeout) {
        return actions.isVisible(SUCCESS, timeout);
    }

    private void hideKeyboard() {
        try {
            driver.hideKeyboard();
        } catch (org.openqa.selenium.WebDriverException e) {
            // no keyboard showing: nothing to hide
        }
    }

    private void backToMenu() {
        for (int i = 0; i < 3 && !actions.isVisible(TO_OTHER_BANKS, Duration.ofSeconds(2)); i++) {
            driver.navigate().back();
        }
    }

    private boolean searchBank(String bankName, By result) {
        actions.tap(TO_OTHER_BANKS);
        actions.waitVisible(AppiumBy.androidUIAutomator("new UiSelector().descriptionContains(\"Bank\")"));
        actions.tap(SEARCH_ICON);
        for (int attempt = 0; attempt < SEARCH_ATTEMPTS; attempt++) {
            actions.type(BANK_SEARCH, bankName);
            if (actions.isVisible(result, Duration.ofSeconds(4))) {
                return true;
            }
        }
        return false;
    }

    private SendMoneyPage fillRecipient(String recipient, String amount) {
        actions.type(SEND_TO, recipient);
        actions.type(AMOUNT, amount);
        actions.tap(AMOUNT_HEADING);
        actions.tap(NEXT);
        return this;
    }

    /** True when the app accepted the recipient and moved to the review step (no money is moved by the tests). */
    public boolean isReviewDisplayed(Duration timeout) {
        return actions.isVisible(REVIEW, timeout);
    }

    private void pushToGallery(File image) {
        try {
            String remote = GALLERY_DIR + image.getName();
            driver.pushFile(remote, image);
            driver.executeScript("mobile: broadcast", Map.of(
                    "action", "android.intent.action.MEDIA_SCANNER_SCAN_FILE", "uri", "file://" + remote));
        } catch (java.io.IOException e) {
            throw new exceptions.FrameworkException("Could not push QR image " + image, e);
        }
    }
}
