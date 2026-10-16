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

    public MobileActions(AndroidDriver driver) {
        this(driver, ConfigManager.get());
    }

    public MobileActions(AndroidDriver driver, ConfigManager cfg) {
        this.driver = driver;
        this.defaultTimeout = cfg.getSeconds("wait.explicit.seconds");
        this.pollInterval = Duration.ofMillis(cfg.getInt("wait.poll.millis"));
    }

    // ---- waits -------------------------------------------------------------------------------------------

    public WebElement waitVisible(By locator) {
        return waitVisible(locator, defaultTimeout);
    }

    public WebElement waitVisible(By locator, Duration timeout) {
        try {
            return newWait(timeout).until(ExpectedConditions.visibilityOfElementLocated(locator));
        } catch (TimeoutException e) {
            throw new FrameworkException("Element not visible within " + timeout.toSeconds() + "s: " + locator, e);
        }
    }

    public WebElement waitClickable(By locator) {
        try {
            return newWait(defaultTimeout).until(ExpectedConditions.elementToBeClickable(locator));
        } catch (TimeoutException e) {
            throw new FrameworkException("Element not clickable within " + defaultTimeout.toSeconds() + "s: " + locator, e);
        }
    }

    /** Non-throwing check: true if the element becomes visible within the timeout. */
    public boolean isVisible(By locator, Duration timeout) {
        try {
            newWait(timeout).until(ExpectedConditions.visibilityOfElementLocated(locator));
            return true;
        } catch (TimeoutException e) {
            return false;
        }
    }

    public boolean isVisible(By locator) {
        return isVisible(locator, defaultTimeout);
    }

    public boolean isVisible(String configuredLocator) {
        return isVisible(LocatorParser.parse(configuredLocator));
    }

    // ---- interactions ------------------------------------------------------------------------------------

    public void tap(By locator) {
        LOG.info("Tap {}", locator);
        waitClickable(locator).click();
    }

    public void type(By locator, String text) {
        if (text == null) {
            throw new IllegalArgumentException("text must not be null (use clear() to empty a field)");
        }
        LOG.info("Type into {} ({} chars)", locator, text.length()); // value intentionally not logged: may be a secret
        WebElement field = waitClickable(locator);
        field.click(); // focus first: Flutter/custom fields only register input once focused
        field.clear();
        field.sendKeys(text);
    }

    public void clear(By locator) {
        LOG.info("Clear {}", locator);
        waitVisible(locator).clear();
    }

    public boolean isEnabled(By locator) {
        return waitVisible(locator).isEnabled();
    }

    public String text(By locator) {
        return waitVisible(locator).getText();
    }

    // ---- gestures ----------------------------------------------------------------------------------------

    /** Swipes across the screen using UiAutomator2's {@code mobile: swipeGesture}. */
    public void swipe(String direction, double percent) {
        String dir = GestureValidator.validateDirection(direction);
        GestureValidator.validatePercent(percent);
        Dimension size = driver.manage().window().getSize();
        LOG.info("Swipe {} {}% on {}x{} screen", dir, (int) (percent * 100), size.width, size.height);
        try {
            driver.executeScript("mobile: swipeGesture", Map.of(
                    "left", (int) (size.width * 0.1),
                    "top", (int) (size.height * 0.1),
                    "width", (int) (size.width * 0.8),
                    "height", (int) (size.height * 0.8),
                    "direction", dir,
                    "percent", percent));
        } catch (WebDriverException e) {
            throw new FrameworkException("Swipe " + dir + " failed", e);
        }
    }

    public void swipe(String direction) {
        swipe(direction, ConfigManager.get().getDouble("swipe.defaultPercent"));
    }

    /**
     * Scrolls a scrollable container until an element with the exact text is visible.
     * Bounded by {@code maxSwipes} so a missing item can never loop forever.
     *
     * @return true if the text was reached, false if it was not found within the bound.
     */
    public boolean scrollToText(String text, int maxSwipes) {
        if (text == null || text.isBlank()) {
            throw new IllegalArgumentException("text must not be blank");
        }
        GestureValidator.validateMaxAttempts(maxSwipes);
        String selector = "new UiScrollable(new UiSelector().scrollable(true).instance(0))"
                + ".setMaxSearchSwipes(" + maxSwipes + ")"
                + ".scrollIntoView(new UiSelector().text(\"" + LocatorParser.escapeUiSelector(text) + "\"))";
        try {
            driver.findElement(AppiumBy.androidUIAutomator(selector));
            return true;
        } catch (org.openqa.selenium.NoSuchElementException e) {
            LOG.warn("Text '{}' not found after {} swipes", text, maxSwipes);
            return false;
        }
    }

    public boolean scrollToText(String text) {
        return scrollToText(text, ConfigManager.get().getInt("scroll.maxAttempts"));
    }

    // ---- diagnostics -------------------------------------------------------------------------------------

    /** Saves a PNG under {@code artifacts.dir/screenshots/<run date-time>} and returns its path. */
    public Path screenshot(String name) {
        return screenshot(null, name);
    }

    /** Same as {@link #screenshot(String)} but saved under {@code screenshots/<run>/<subfolder>} (e.g. PASSED / FAILED). */
    public Path screenshot(String subfolder, String name) {
        Path dir = Paths.get(ConfigManager.get().require("artifacts.dir"), "screenshots", RUN_FOLDER);
        if (subfolder != null && !subfolder.isBlank()) {
            dir = dir.resolve(sanitize(subfolder));
        }
        Path target = dir.resolve(sanitize(name) + "-" + LocalDateTime.now().format(STAMP) + ".png");
        try {
            Files.createDirectories(dir);
            Files.write(target, driver.getScreenshotAs(OutputType.BYTES));
            LOG.info("Screenshot saved: {}", target);
            return target;
        } catch (IOException | WebDriverException e) {
            throw new FrameworkException("Could not capture screenshot '" + name + "'", e);
        }
    }

    public String pageSource() {
        return driver.getPageSource();
    }

    static String sanitize(String name) {
        String clean = name == null ? "" : name.replaceAll("[^A-Za-z0-9._-]", "_");
        return clean.isEmpty() ? "unnamed" : clean;
    }

    private WebDriverWait newWait(Duration timeout) {
        if (timeout == null || timeout.isNegative() || timeout.isZero()) {
            throw new IllegalArgumentException("timeout must be positive but was " + timeout);
        }
        WebDriverWait wait = new WebDriverWait(driver, timeout);
        wait.pollingEvery(pollInterval);
        return wait;
    }
}
