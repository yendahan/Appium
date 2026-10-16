package actions;

import config.ConfigManager;
import exceptions.FrameworkException;
import io.appium.java_client.AppiumBy;
import io.appium.java_client.android.AndroidDriver;
import org.openqa.selenium.By;
import org.openqa.selenium.Dimension;
import org.openqa.selenium.OutputType;
import org.openqa.selenium.TimeoutException;
import org.openqa.selenium.WebDriverException;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.support.ui.ExpectedConditions;
import org.openqa.selenium.support.ui.WebDriverWait;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import utils.LocatorParser;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.time.Duration;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.Map;

/** Reusable, explicitly-waiting UI actions. All page objects delegate to this class. */
public class MobileActions {

    private static final Logger LOG = LoggerFactory.getLogger(MobileActions.class);
    private static final DateTimeFormatter STAMP = DateTimeFormatter.ofPattern("yyyyMMdd-HHmmss-SSS");
    /** One folder per test run (JVM), e.g. {@code screenshots/2026-10-16_14-30-00/PASSED}. */
    private static final String RUN_FOLDER =
            LocalDateTime.now().format(DateTimeFormatter.ofPattern("yyyy-MM-dd_HH-mm-ss"));

    private final AndroidDriver driver;
    private final Duration defaultTimeout;
    private final Duration pollInterval;

    /**
     * Creates actions bound to a driver, using the shared configuration.
     *
     * @param driver the active Android session
     */
    public MobileActions(AndroidDriver driver) {
        // Delegate to the full constructor with the global configuration.
        this(driver, ConfigManager.get());
    }

    /**
     * Creates actions bound to a driver and a specific configuration.
     *
     * @param driver the active Android session
     * @param cfg    configuration providing wait timeout and polling interval
     * @throws FrameworkException if the wait settings are missing or invalid
     */
    public MobileActions(AndroidDriver driver, ConfigManager cfg) {
        // Keep the session that every action will operate on.
        this.driver = driver;
        // Default max wait for all explicit waits, from config so it can be tuned per environment.
        this.defaultTimeout = cfg.getSeconds("wait.explicit.seconds");
        // How often waits re-check the condition.
        this.pollInterval = Duration.ofMillis(cfg.getInt("wait.poll.millis"));
    }

    // ---- waits -------------------------------------------------------------------------------------------

    /**
     * Waits for an element to be visible using the default timeout.
     *
     * @param locator how to find the element
     * @return the visible element
     * @throws FrameworkException if it does not appear in time
     */
    public WebElement waitVisible(By locator) {
        // Reuse the timeout overload so behaviour stays in one place.
        return waitVisible(locator, defaultTimeout);
    }

    /**
     * Waits for an element to be visible.
     *
     * @param locator how to find the element
     * @param timeout maximum time to wait; must be positive
     * @return the visible element
     * @throws FrameworkException if it does not appear within the timeout
     */
    public WebElement waitVisible(By locator, Duration timeout) {
        try {
            // Poll until the element is present and displayed.
            return newWait(timeout).until(ExpectedConditions.visibilityOfElementLocated(locator));
        } catch (TimeoutException e) {
            // Convert to a framework error that names the locator and the time waited.
            throw new FrameworkException("Element not visible within " + timeout.toSeconds() + "s: " + locator, e);
        }
    }

    /**
     * Waits for an element to be visible and enabled, using the default timeout.
     *
     * @param locator how to find the element
     * @return the clickable element
     * @throws FrameworkException if it does not become clickable in time
     */
    public WebElement waitClickable(By locator) {
        try {
            // Clickable means visible and enabled, which avoids taps on disabled buttons.
            return newWait(defaultTimeout).until(ExpectedConditions.elementToBeClickable(locator));
        } catch (TimeoutException e) {
            // Convert to a framework error that names the locator and the time waited.
            throw new FrameworkException("Element not clickable within " + defaultTimeout.toSeconds() + "s: " + locator, e);
        }
    }

    /**
     * Non-throwing check: true if the element becomes visible within the timeout.
     *
     * @param locator how to find the element
     * @param timeout maximum time to wait; must be positive
     * @return true if visible in time, false otherwise
     */
    public boolean isVisible(By locator, Duration timeout) {
        try {
            // Same wait as waitVisible, but the result is only used as a yes/no.
            newWait(timeout).until(ExpectedConditions.visibilityOfElementLocated(locator));
            // Reaching here means the element appeared.
            return true;
        } catch (TimeoutException e) {
            // A timeout is an expected "no" for this method, so it is not rethrown.
            return false;
        }
    }

    /**
     * Non-throwing visibility check using the default timeout.
     *
     * @param locator how to find the element
     * @return true if visible in time, false otherwise
     */
    public boolean isVisible(By locator) {
        // Reuse the timeout overload with the configured default.
        return isVisible(locator, defaultTimeout);
    }

    /**
     * Non-throwing visibility check for a "strategy=value" locator string from configuration.
     *
     * @param configuredLocator locator in the format understood by {@link LocatorParser}
     * @return true if visible in time, false otherwise
     * @throws FrameworkException if the locator string is malformed
     */
    public boolean isVisible(String configuredLocator) {
        // Convert the text to a By and reuse the standard check.
        return isVisible(LocatorParser.parse(configuredLocator));
    }

    // ---- interactions ------------------------------------------------------------------------------------

    /**
     * Taps an element once it is clickable.
     * Side effect: performs a click on the device, which may trigger real app actions.
     *
     * @param locator how to find the element
     * @throws FrameworkException if it does not become clickable in time
     */
    public void tap(By locator) {
        // Log the target to make test runs traceable.
        LOG.info("Tap {}", locator);
        // Wait first so the tap never lands on an element that is not ready.
        waitClickable(locator).click();
    }

    /**
     * Replaces the contents of a text field.
     * Side effect: types on the device; the text itself is deliberately not logged.
     *
     * @param locator how to find the field
     * @param text    the text to enter; must not be null
     * @throws IllegalArgumentException if text is null
     * @throws FrameworkException       if the field does not become clickable in time
     */
    public void type(By locator, String text) {
        // Guard against accidental nulls; clearing a field has its own method.
        if (text == null) {
            throw new IllegalArgumentException("text must not be null (use clear() to empty a field)");
        }
        // Log only the length because the text may be a password.
        LOG.info("Type into {} ({} chars)", locator, text.length()); // value intentionally not logged: may be a secret
        // Wait until the field can accept input.
        WebElement field = waitClickable(locator);
        // Focus the field before typing.
        field.click(); // focus first: Flutter/custom fields only register input once focused
        // Remove any existing text so the result is exactly the supplied value.
        field.clear();
        // Enter the new text.
        field.sendKeys(text);
    }

    /**
     * Empties a text field.
     * Side effect: modifies the field on the device.
     *
     * @param locator how to find the field
     * @throws FrameworkException if the field does not become visible in time
     */
    public void clear(By locator) {
        // Log the target to make test runs traceable.
        LOG.info("Clear {}", locator);
        // Wait for the field, then clear it.
        waitVisible(locator).clear();
    }

    /**
     * Reports whether an element is enabled.
     *
     * @param locator how to find the element
     * @return true if the element is enabled
     * @throws FrameworkException if it does not become visible in time
     */
    public boolean isEnabled(By locator) {
        // Wait until visible so the enabled state is read from a rendered element.
        return waitVisible(locator).isEnabled();
    }

    /**
     * Reads the visible text of an element.
     *
     * @param locator how to find the element
     * @return the element's text
     * @throws FrameworkException if it does not become visible in time
     */
    public String text(By locator) {
        // Wait until visible so the text is read from a rendered element.
        return waitVisible(locator).getText();
    }

    // ---- gestures ----------------------------------------------------------------------------------------

    /**
     * Swipes across the screen using UiAutomator2's {@code mobile: swipeGesture}.
     * Side effect: performs a swipe on the device, which may scroll or navigate in the app.
     *
     * @param direction one of up, down, left, right (case-insensitive)
     * @param percent   fraction of the swipe area to travel, in (0, 1]
     * @throws IllegalArgumentException if direction or percent is invalid
     * @throws FrameworkException       if the device rejects the gesture
     */
    public void swipe(String direction, double percent) {
        // Validate and normalise the direction before touching the device.
        String dir = GestureValidator.validateDirection(direction);
        // Validate the distance for the same reason.
        GestureValidator.validatePercent(percent);
        // Screen size is needed to compute a swipe area that works on any device.
        Dimension size = driver.manage().window().getSize();
        // Log the gesture details for traceability.
        LOG.info("Swipe {} {}% on {}x{} screen", dir, (int) (percent * 100), size.width, size.height);
        try {
            // Swipe inside an 80% central area to avoid system edge gestures (back/home).
            driver.executeScript("mobile: swipeGesture", Map.of(
                    "left", (int) (size.width * 0.1),
                    "top", (int) (size.height * 0.1),
                    "width", (int) (size.width * 0.8),
                    "height", (int) (size.height * 0.8),
                    "direction", dir,
                    "percent", percent));
        } catch (WebDriverException e) {
            // Wrap driver errors with the gesture that failed.
            throw new FrameworkException("Swipe " + dir + " failed", e);
        }
    }

    /**
     * Swipes using the configured default distance ({@code swipe.defaultPercent}).
     *
     * @param direction one of up, down, left, right (case-insensitive)
     * @throws IllegalArgumentException if the direction or configured percent is invalid
     * @throws FrameworkException       if the setting is missing or the device rejects the gesture
     */
    public void swipe(String direction) {
        // Read the default distance from config so it can be tuned without code changes.
        swipe(direction, ConfigManager.get().getDouble("swipe.defaultPercent"));
    }

    /**
     * Scrolls a scrollable container until an element with the exact text is visible.
     * Bounded by {@code maxSwipes} so a missing item can never loop forever.
     * Side effect: scrolls the screen on the device.
     *
     * @param text      exact visible text to find; must not be blank
     * @param maxSwipes maximum number of swipes, at least 1
     * @return true if the text was reached, false if it was not found within the bound.
     * @throws IllegalArgumentException if text is blank or maxSwipes is below 1
     */
    public boolean scrollToText(String text, int maxSwipes) {
        // Reject blank text because it would match arbitrary elements.
        if (text == null || text.isBlank()) {
            throw new IllegalArgumentException("text must not be blank");
        }
        // Ensure the bound allows at least one swipe.
        GestureValidator.validateMaxAttempts(maxSwipes);
        // Build a UiScrollable selector that scrolls the first scrollable view until the text shows; escape the text so quotes cannot break it.
        String selector = "new UiScrollable(new UiSelector().scrollable(true).instance(0))"
                + ".setMaxSearchSwipes(" + maxSwipes + ")"
                + ".scrollIntoView(new UiSelector().text(\"" + LocatorParser.escapeUiSelector(text) + "\"))";
        try {
            // Finding the element triggers the scrolling on the device.
            driver.findElement(AppiumBy.androidUIAutomator(selector));
            // No exception means the text was reached.
            return true;
        } catch (org.openqa.selenium.NoSuchElementException e) {
            // Not found within the bound is an expected "no", so log and return false.
            LOG.warn("Text '{}' not found after {} swipes", text, maxSwipes);
            return false;
        }
    }

    /**
     * Scrolls to the text using the configured bound ({@code scroll.maxAttempts}).
     *
     * @param text exact visible text to find
     * @return true if the text was reached, false otherwise
     * @throws IllegalArgumentException if text is blank
     * @throws FrameworkException       if the setting is missing or invalid
     */
    public boolean scrollToText(String text) {
        // Read the bound from config so it can be tuned without code changes.
        return scrollToText(text, ConfigManager.get().getInt("scroll.maxAttempts"));
    }

    // ---- diagnostics -------------------------------------------------------------------------------------

    /**
     * Saves a PNG under {@code artifacts.dir/screenshots/<run date-time>} and returns its path.
     * Side effect: writes a file to disk.
     *
     * @param name base name for the file (sanitised)
     * @return the path of the saved screenshot
     * @throws FrameworkException if the screenshot cannot be captured or written
     */
    public Path screenshot(String name) {
        // No subfolder: save directly in the run folder.
        return screenshot(null, name);
    }

    /**
     * Same as {@link #screenshot(String)} but saved under {@code screenshots/<run>/<subfolder>} (e.g. PASSED / FAILED).
     * Side effect: creates directories and writes a file to disk.
     *
     * @param subfolder optional subfolder name (sanitised); null or blank means none
     * @param name      base name for the file (sanitised)
     * @return the path of the saved screenshot
     * @throws FrameworkException if the screenshot cannot be captured or written
     */
    public Path screenshot(String subfolder, String name) {
        // Group all screenshots of this run under one folder so runs do not mix.
        Path dir = Paths.get(ConfigManager.get().require("artifacts.dir"), "screenshots", RUN_FOLDER);
        // Add the optional subfolder, e.g. PASSED or FAILED.
        if (subfolder != null && !subfolder.isBlank()) {
            // Sanitise so user-supplied names cannot escape the folder.
            dir = dir.resolve(sanitize(subfolder));
        }
        // A millisecond timestamp keeps file names unique when a test takes several shots.
        Path target = dir.resolve(sanitize(name) + "-" + LocalDateTime.now().format(STAMP) + ".png");
        try {
            // Make sure the folder exists before writing.
            Files.createDirectories(dir);
            // Capture the screen as PNG bytes and save them.
            Files.write(target, driver.getScreenshotAs(OutputType.BYTES));
            // Record the location for easy retrieval.
            LOG.info("Screenshot saved: {}", target);
            // Return the path so callers (e.g. the listener) can link to it.
            return target;
        } catch (IOException | WebDriverException e) {
            // Wrap both disk and driver failures with the screenshot name.
            throw new FrameworkException("Could not capture screenshot '" + name + "'", e);
        }
    }

    /**
     * Returns the current UI hierarchy as XML, useful for debugging locators.
     *
     * @return the page source
     */
    public String pageSource() {
        // Ask the driver for the current screen's XML.
        return driver.getPageSource();
    }

    /**
     * Makes a string safe to use as a file or folder name.
     *
     * @param name the raw name, may be null
     * @return the name with unsafe characters replaced by underscores, or "unnamed" if empty
     */
    static String sanitize(String name) {
        // Replace anything outside a conservative character set to prevent path tricks and invalid names.
        String clean = name == null ? "" : name.replaceAll("[^A-Za-z0-9._-]", "_");
        // Never return an empty name, which would produce a hidden or invalid file.
        return clean.isEmpty() ? "unnamed" : clean;
    }

    /**
     * Creates a configured explicit wait.
     *
     * @param timeout maximum time to wait; must be positive
     * @return a wait using the configured polling interval
     * @throws IllegalArgumentException if timeout is null, zero or negative
     */
    private WebDriverWait newWait(Duration timeout) {
        // A non-positive timeout would make waits return instantly and hide real problems.
        if (timeout == null || timeout.isNegative() || timeout.isZero()) {
            throw new IllegalArgumentException("timeout must be positive but was " + timeout);
        }
        // Bind the wait to this session with the requested limit.
        WebDriverWait wait = new WebDriverWait(driver, timeout);
        // Use the configured poll interval instead of the slower default.
        wait.pollingEvery(pollInterval);
        // Return the ready wait.
        return wait;
    }
}
