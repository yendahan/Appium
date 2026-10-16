package utils;

import exceptions.FrameworkException;
import io.appium.java_client.AppiumBy;
import org.openqa.selenium.By;

/**
 * Converts "strategy=value" strings from configuration into a {@link By}.
 * Supported strategies: id, accessibilityId, xpath, text (exact visible text), className.
 */
public final class LocatorParser {

    /** Utility class; not instantiable. */
    private LocatorParser() {
    }

    /**
     * Parses a "strategy=value" string into an Appium locator.
     *
     * @param raw the configured locator, e.g. {@code id=com.app:id/login}
     * @return the matching {@link By}
     * @throws FrameworkException if the string is empty, malformed, has an empty value or an unknown strategy
     */
    public static By parse(String raw) {
        // Fail fast on missing config so the error points at the locator, not a later timeout.
        if (raw == null || raw.isBlank()) {
            throw new FrameworkException("Locator is empty. Expected format 'strategy=value'");
        }
        // Split on the first '=' only, because values (e.g. xpath) may contain further '=' characters.
        int idx = raw.indexOf('=');
        // idx <= 0 means there is no '=' or no strategy before it.
        if (idx <= 0) {
            throw new FrameworkException("Invalid locator '" + raw + "'. Expected format 'strategy=value'");
        }
        // Everything before the first '=' names the lookup strategy.
        String strategy = raw.substring(0, idx).trim();
        // Everything after it is the lookup value, passed through unchanged apart from trimming.
        String value = raw.substring(idx + 1).trim();
        // A strategy with no value can never match an element.
        if (value.isEmpty()) {
            throw new FrameworkException("Locator '" + raw + "' has an empty value");
        }
        // Map the strategy name to the corresponding Appium/Selenium locator type.
        return switch (strategy) {
            case "id" -> AppiumBy.id(value);
            case "accessibilityId" -> AppiumBy.accessibilityId(value);
            case "xpath" -> AppiumBy.xpath(value);
            case "className" -> AppiumBy.className(value);
            // "text" has no native By, so build a UiAutomator selector for exact visible text.
            case "text" -> AppiumBy.androidUIAutomator(
                    "new UiSelector().text(\"" + escapeUiSelector(value) + "\")");
            // Unknown strategies are reported with the supported list rather than silently ignored.
            default -> throw new FrameworkException("Unsupported locator strategy '" + strategy + "' in '" + raw
                    + "'. Use id, accessibilityId, xpath, className or text");
        };
    }

    /**
     * Escapes characters that would break a UiSelector string literal.
     *
     * @param value raw text to embed inside a double-quoted UiSelector string
     * @return the text with backslashes and double quotes escaped
     */
    public static String escapeUiSelector(String value) {
        // Escape backslashes first so the backslashes added for quotes are not escaped twice.
        return value.replace("\\", "\\\\").replace("\"", "\\\"");
    }
}
