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

    // Home-screen entry to the services menu.
    private static final By SERVICES = AppiumBy.accessibilityId("Services");
    // Services menu tile that opens Send Money.
    private static final By SEND_MONEY = AppiumBy.accessibilityId("Send Money");
    // Option to pay by uploading a QR code.
    private static final By VIA_QR = AppiumBy.accessibilityId("Via QR");
    // Option to send to another Bayad wallet by number.
    private static final By TO_BAYAD_WALLET = AppiumBy.accessibilityId("To Bayad Wallet");
    // Option to send to a bank or e-wallet; also the marker that the options menu is showing.
    private static final By TO_OTHER_BANKS = AppiumBy.accessibilityId("To Other Banks and E-Wallets");
    // Opens the gallery picker for a QR image.
    private static final By UPLOAD_QR = AppiumBy.accessibilityId("Upload QR from Gallery");
    // Recipient field on the wallet form (found by hint, no accessibility id).
    private static final By SEND_TO = AppiumBy.xpath("//android.widget.EditText[@hint='Send money to']");
    // Amount field on the wallet form.
    private static final By AMOUNT = AppiumBy.xpath("//android.widget.EditText[@hint='Enter cash amount']");
    // Bank account number field.
    private static final By ACCOUNT_NO = AppiumBy.xpath("//android.widget.EditText[@hint='Account No.']");
    // Amount field on the bank/QR form (hint differs from the wallet form).
    private static final By BANK_AMOUNT = AppiumBy.xpath("//android.widget.EditText[@hint='Amount']");
    // Bank account name field; also tapped to blur other fields.
    private static final By ACCOUNT_NAME = AppiumBy.xpath("//android.widget.EditText[@hint='Account Name']");
    // First photo in the picker, which is the newest, i.e. the QR image just pushed.
    private static final By NEWEST_PHOTO = AppiumBy.androidUIAutomator(
            "new UiSelector().descriptionStartsWith(\"Photo taken\").instance(0)");
    // Confirms the picker selection; may be exposed as text or content-desc, so match both.
    private static final By PICKER_DONE = AppiumBy.xpath("//*[@text='Done' or @content-desc='Done']");
    // Static heading tapped to drop focus from the amount field.
    private static final By AMOUNT_HEADING = AppiumBy.accessibilityId("Enter or Select Amount (Php)");
    // Opens search in the bank list; the button has no label, so it is found by position.
    private static final By SEARCH_ICON = AppiumBy.xpath("(//android.widget.Button)[2]"); // unlabeled, top right
    // Search box in the bank list; the only EditText on that screen.
    private static final By BANK_SEARCH = AppiumBy.className("android.widget.EditText");
    // Receipt banner; contains-match because the reference number is appended.
    private static final By SUCCESS = AppiumBy.xpath("//*[contains(@content-desc,'Successfully Sent')]");
    // Final button that actually sends the money.
    private static final By CONFIRM = AppiumBy.accessibilityId("CONFIRM");
    // Advances from a form to the review step.
    private static final By NEXT = AppiumBy.accessibilityId("NEXT");
    // Review screen heading; its title differs between wallet and bank flows.
    private static final By REVIEW = AppiumBy.xpath(
            "//*[@content-desc='Send Money Confirmation' or @content-desc='Payment Confirmation']");

    // Retries typing the search term, since the filtered list can lag.
    private static final int SEARCH_ATTEMPTS = 2;
    // Times the whole bank list is reopened when the backend returns an incomplete list.
    private static final int BANK_LIST_ATTEMPTS = 3;
    // Emulator folder scanned by the gallery app.
    private static final String GALLERY_DIR = "/sdcard/Pictures/";

    /**
     * Creates the page object; does not interact with the app.
     *
     * @param driver the active Android driver session
     */
    public SendMoneyPage(AndroidDriver driver) {
        super(driver);
    }

    /**
     * From the home screen: Services &gt; Send Money.
     * Side effect: navigates to the Send Money options menu.
     *
     * @return this page, for chaining
     */
    public SendMoneyPage open() {
        // Open the services menu, then pick Send Money.
        actions.tap(SERVICES);
        actions.tap(SEND_MONEY);
        return this;
    }

    /**
     * Sends via QR: pushes the image to the emulator gallery, picks it, fills the amount if needed and taps NEXT.
     * Side effects: writes the image to the device storage and advances to the review step (no CONFIRM).
     *
     * @param qrImage local QR image file to upload
     * @param amount  amount to enter when the QR does not carry one
     * @return this page, for chaining
     */
    public SendMoneyPage viaQr(File qrImage, String amount) {
        // Choose the QR option, then make the image available to the picker.
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
        // Read the amount field to tell dynamic QR (prefilled) from static QR (empty or showing the hint).
        String prefilled = actions.text(BANK_AMOUNT);
        if (prefilled.isBlank() || prefilled.equals("Amount")) {
            actions.type(BANK_AMOUNT, amount);
            actions.tap(ACCOUNT_NAME);
        }
        actions.tap(NEXT);
        return this;
    }

    /**
     * Sends to a Bayad wallet: fills recipient and amount and taps NEXT.
     * Side effect: advances to the review step (no CONFIRM).
     *
     * @param number recipient wallet number
     * @param amount amount to send
     * @return this page, for chaining
     */
    public SendMoneyPage toBayadWallet(String number, String amount) {
        // Choose the wallet option, then share the common recipient/amount form logic.
        actions.tap(TO_BAYAD_WALLET);
        return fillRecipient(number, amount);
    }

    /**
     * Picks the bank from the "Banks &amp; Wallets" list (each row's description is "&lt;name&gt;\nBank"),
     * fills the account details and taps NEXT.
     * Side effect: advances to the review step (no CONFIRM).
     *
     * @param accountNumber destination account number
     * @param accountName   destination account name
     * @param bankName      bank or e-wallet name as shown in the list (prefix match)
     * @param amount        amount to send
     * @return this page, for chaining
     */
    public SendMoneyPage toOtherBank(String accountNumber, String accountName, String bankName, String amount) {
        // Row locator: match on the description prefix because the row also contains the "Bank" suffix.
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

    /**
     * Taps CONFIRM on the review screen.
     * Side effect: MOVES REAL MONEY (Php 10 on staging); call only from tests meant to do so.
     *
     * @return this page, for chaining
     */
    public SendMoneyPage confirm() {
        // Final, irreversible step of the flow.
        actions.tap(CONFIRM);
        return this;
    }

    /**
     * True when the receipt ("Successfully Sent!" with the reference number) is shown after CONFIRM.
     *
     * @param timeout maximum time to wait for the receipt
     * @return true if the receipt appeared before the timeout
     */
    public boolean isReceiptDisplayed(Duration timeout) {
        return actions.isVisible(SUCCESS, timeout);
    }

    /**
     * Hides the soft keyboard if present.
     * Side effect: may close the keyboard; never fails when none is showing.
     */
    private void hideKeyboard() {
        try {
            // Direct driver call: hiding the keyboard is a system action, not an element interaction.
            driver.hideKeyboard();
        } catch (org.openqa.selenium.WebDriverException e) {
            // no keyboard showing: nothing to hide
        }
    }

    /**
     * Presses Back (at most 3 times; the first press only closes the keyboard) until the Send Money options show again.
     * Side effect: navigates backwards in the app.
     */
    private void backToMenu() {
        // Stop as soon as the options menu is visible so we never back out of Send Money.
        for (int i = 0; i < 3 && !actions.isVisible(TO_OTHER_BANKS, Duration.ofSeconds(2)); i++) {
            driver.navigate().back();
        }
    }

    /**
     * Opens the bank list, searches for the bank and checks the row appeared.
     * Side effects: navigates into the list and types into the search box.
     *
     * @param bankName bank name to search for
     * @param result   locator of the expected list row
     * @return true if the row was found, false if the list stayed incomplete
     */
    private boolean searchBank(String bankName, By result) {
        // Open the list and wait until it has loaded (rows describe themselves as banks).
        actions.tap(TO_OTHER_BANKS);
        actions.waitVisible(AppiumBy.androidUIAutomator("new UiSelector().descriptionContains(\"Bank\")"));
        actions.tap(SEARCH_ICON);
        // Retype the term if the filtered row does not show up.
        for (int attempt = 0; attempt < SEARCH_ATTEMPTS; attempt++) {
            actions.type(BANK_SEARCH, bankName);
            if (actions.isVisible(result, Duration.ofSeconds(4))) {
                return true;
            }
        }
        return false;
    }

    /**
     * Fills the wallet form (recipient and amount) and taps NEXT.
     * Side effect: advances to the review step.
     *
     * @param recipient recipient wallet number
     * @param amount    amount to send
     * @return this page, for chaining
     */
    private SendMoneyPage fillRecipient(String recipient, String amount) {
        // Fill both fields, tap a neutral heading to commit the amount, then advance.
        actions.type(SEND_TO, recipient);
        actions.type(AMOUNT, amount);
        actions.tap(AMOUNT_HEADING);
        actions.tap(NEXT);
        return this;
    }

    /**
     * True when the app accepted the recipient and moved to the review step (no money is moved by the tests).
     *
     * @param timeout maximum time to wait for the review screen
     * @return true if the review screen appeared before the timeout
     */
    public boolean isReviewDisplayed(Duration timeout) {
        return actions.isVisible(REVIEW, timeout);
    }

    /**
     * Copies an image into the emulator gallery and triggers a media scan so the picker lists it.
     * Side effects: writes to device storage and sends a broadcast.
     *
     * @param image local file to push
     * @throws exceptions.FrameworkException if the file cannot be pushed
     */
    private void pushToGallery(File image) {
        try {
            // Same file name on the device so the picker shows a recognizable photo.
            String remote = GALLERY_DIR + image.getName();
            driver.pushFile(remote, image);
            // Ask the media scanner to index the file now (avoids adb shell, which the server disallows).
            driver.executeScript("mobile: broadcast", Map.of(
                    "action", "android.intent.action.MEDIA_SCANNER_SCAN_FILE", "uri", "file://" + remote));
        } catch (java.io.IOException e) {
            // Wrap the checked error so tests fail with a clear framework message.
            throw new exceptions.FrameworkException("Could not push QR image " + image, e);
        }
    }
}
