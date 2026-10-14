package utils;

import exceptions.FrameworkException;
import io.appium.java_client.AppiumBy;
import org.openqa.selenium.By;

/**
 * Converts "strategy=value" strings from configuration into a {@link By}.
 * Supported strategies: id, accessibilityId, xpath, text (exact visible text), className.
 */
public final class LocatorParser {

    private LocatorParser() {
    }

    public static By parse(String raw) {
        if (raw == null || raw.isBlank()) {
            throw new FrameworkException("Locator is empty. Expected format 'strategy=value'");
        }
        int idx = raw.indexOf('=');
        if (idx <= 0) {
            throw new FrameworkException("Invalid locator '" + raw + "'. Expected format 'strategy=value'");
        }
        String strategy = raw.substring(0, idx).trim();
        String value = raw.substring(idx + 1).trim();
        if (value.isEmpty()) {
            throw new FrameworkException("Locator '" + raw + "' has an empty value");
        }
        return switch (strategy) {
            case "id" -> AppiumBy.id(value);
            case "accessibilityId" -> AppiumBy.accessibilityId(value);
            case "xpath" -> AppiumBy.xpath(value);
            case "className" -> AppiumBy.className(value);
            case "text" -> AppiumBy.androidUIAutomator(
                    "new UiSelector().text(\"" + escapeUiSelector(value) + "\")");
            default -> throw new FrameworkException("Unsupported locator strategy '" + strategy + "' in '" + raw
                    + "'. Use id, accessibilityId, xpath, className or text");
        };
    }

    /** Escapes characters that would break a UiSelector string literal. */
    public static String escapeUiSelector(String value) {
        return value.replace("\\", "\\\\").replace("\"", "\\\"");
    }
}
