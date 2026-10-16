package config;

import exceptions.FrameworkException;

import java.io.IOException;
import java.io.InputStream;
import java.time.Duration;
import java.util.Properties;

/**
 * Layered configuration. Precedence (highest first):
 * JVM -Dkey, environment variable (KEY_WITH_UNDERSCORES), device profile, env profile, defaults.
 * Profiles are selected with -Denv (default "qa") and -Ddevice (default "emulator").
 */
public final class ConfigManager {

    public static final String DEFAULT_ENV = "qa";
    public static final String DEFAULT_DEVICE = "emulator";

    private final Properties merged = new Properties();
    private final String env;
    private final String device;

    /** Lazy, thread-safe singleton holder: the instance is created on first use of {@link #get()}. */
    private static final class Holder {
        static final ConfigManager INSTANCE = new ConfigManager(
                System.getProperty("env", DEFAULT_ENV), System.getProperty("device", DEFAULT_DEVICE));
    }

    /**
     * Returns the shared configuration for the current JVM.
     *
     * @return the singleton built from {@code -Denv} and {@code -Ddevice}
     */
    public static ConfigManager get() {
        // Class loading of Holder guarantees a single, safely published instance.
        return Holder.INSTANCE;
    }

    /**
     * Builds a configuration for the given profiles. Visible for tests that need an isolated instance.
     * Side effect: reads three property files from the classpath.
     *
     * @param env    environment profile name; blank falls back to {@link #DEFAULT_ENV}
     * @param device device profile name; blank falls back to {@link #DEFAULT_DEVICE}
     * @throws FrameworkException if a profile file is missing or unreadable
     */
    public ConfigManager(String env, String device) {
        // Normalise the env name so blank values do not produce a bad file path.
        this.env = blankToDefault(env, DEFAULT_ENV);
        // Normalise the device name for the same reason.
        this.device = blankToDefault(device, DEFAULT_DEVICE);
        // Load defaults first; later files override earlier keys.
        load("config/default.properties");
        // Environment profile overrides defaults.
        load("config/env/" + this.env + ".properties");
        // Device profile overrides the environment profile.
        load("config/devices/" + this.device + ".properties");
    }

    /**
     * Returns the active environment profile name.
     *
     * @return the env name, e.g. "qa"
     */
    public String env() {
        // Expose the normalised value chosen at construction.
        return env;
    }

    /**
     * Returns the active device profile name.
     *
     * @return the device name, e.g. "emulator"
     */
    public String device() {
        // Expose the normalised value chosen at construction.
        return device;
    }

    /**
     * Looks up a setting using the precedence order (JVM property, env var, profile files).
     *
     * @param key the property key, e.g. {@code appium.url}
     * @return the trimmed value, or an empty string when not configured
     */
    public String get(String key) {
        // Highest priority: a -Dkey=value passed on the command line.
        String override = System.getProperty(key);
        // Ignore blank overrides so an empty -D does not wipe out a real value.
        if (isPresent(override)) {
            return override.trim();
        }
        // Next: an environment variable such as APPIUM_URL, handy for CI and secrets.
        String fromEnv = System.getenv(toEnvName(key));
        // Same blank check as above.
        if (isPresent(fromEnv)) {
            return fromEnv.trim();
        }
        // Finally: the merged profile files, defaulting to empty so callers never see null.
        return merged.getProperty(key, "").trim();
    }

    /**
     * Tells whether a setting has a non-empty value.
     *
     * @param key the property key
     * @return true if {@link #get(String)} returns something non-empty
     */
    public boolean has(String key) {
        // Reuse get() so the same precedence rules apply.
        return !get(key).isEmpty();
    }

    /**
     * Returns a mandatory setting or fails fast with an actionable message.
     *
     * @param key the property key
     * @return the non-empty value
     * @throws FrameworkException if the setting is missing, listing where it can be set
     */
    public String require(String key) {
        // Resolve using the normal precedence rules.
        String value = get(key);
        // An empty value means the setting is absent everywhere.
        if (value.isEmpty()) {
            // Tell the user every place the key can be provided.
            throw new FrameworkException("Missing required config '" + key + "'. Set it in config/env/" + env
                    + ".properties, config/devices/" + device + ".properties, via -D" + key + "=..., or env var "
                    + toEnvName(key) + ".");
        }
        // Return the validated value.
        return value;
    }

    /**
     * Returns a mandatory setting as an integer.
     *
     * @param key the property key
     * @return the parsed integer
     * @throws FrameworkException if the setting is missing or not an integer
     */
    public int getInt(String key) {
        // Fail early if the setting is absent.
        String value = require(key);
        try {
            // Convert the text to a number.
            return Integer.parseInt(value);
        } catch (NumberFormatException e) {
            // Report the key and bad value rather than a bare parse error.
            throw new FrameworkException("Config '" + key + "' must be an integer but was '" + value + "'", e);
        }
    }

    /**
     * Returns a mandatory setting as a decimal number.
     *
     * @param key the property key
     * @return the parsed double
     * @throws FrameworkException if the setting is missing or not numeric
     */
    public double getDouble(String key) {
        // Fail early if the setting is absent.
        String value = require(key);
        try {
            // Convert the text to a number.
            return Double.parseDouble(value);
        } catch (NumberFormatException e) {
            // Report the key and bad value rather than a bare parse error.
            throw new FrameworkException("Config '" + key + "' must be a number but was '" + value + "'", e);
        }
    }

    /**
     * Returns an optional boolean setting.
     *
     * @param key the property key
     * @return true only for "true" (any case); false when unset or "false"
     * @throws FrameworkException if the value is anything else
     */
    public boolean getBoolean(String key) {
        // Optional flag: unset behaves as false.
        String value = get(key);
        // Treat unset and explicit "false" the same.
        if (value.isEmpty() || value.equalsIgnoreCase("false")) {
            return false;
        }
        // Explicit "true" enables the flag.
        if (value.equalsIgnoreCase("true")) {
            return true;
        }
        // Reject typos like "yes" instead of silently guessing.
        throw new FrameworkException("Config '" + key + "' must be true or false but was '" + value + "'");
    }

    /**
     * Returns a mandatory positive integer setting as a {@link Duration} in seconds.
     *
     * @param key the property key
     * @return the duration
     * @throws FrameworkException if the setting is missing, not an integer or not greater than zero
     */
    public Duration getSeconds(String key) {
        // Parse via getInt for consistent validation and messages.
        int seconds = getInt(key);
        // Zero or negative timeouts would break waits, so reject them here.
        if (seconds <= 0) {
            throw new FrameworkException("Config '" + key + "' must be > 0 but was " + seconds);
        }
        // Convert to a Duration for use with WebDriverWait.
        return Duration.ofSeconds(seconds);
    }

    /**
     * Converts a dotted property key to its environment variable name.
     *
     * @param key the property key, e.g. {@code appium.url}
     * @return the variable name, e.g. {@code APPIUM_URL}
     */
    static String toEnvName(String key) {
        // Environment variables cannot contain dots and are conventionally upper case.
        return key.toUpperCase().replace('.', '_');
    }

    /**
     * Loads a properties file from the classpath into the merged settings.
     * Side effect: overwrites any previously loaded keys with the same name.
     *
     * @param resource classpath-relative path of the properties file
     * @throws FrameworkException if the file is missing or cannot be read
     */
    private void load(String resource) {
        // Try-with-resources closes the stream; the context loader finds files in src/test/resources.
        try (InputStream in = Thread.currentThread().getContextClassLoader().getResourceAsStream(resource)) {
            // A null stream means the file does not exist, usually from a mistyped profile name.
            if (in == null) {
                throw new FrameworkException("Config resource '" + resource
                        + "' not found on classpath (unknown -Denv or -Ddevice profile?)");
            }
            // Parse into a temporary object first.
            Properties props = new Properties();
            // Read key=value pairs from the file.
            props.load(in);
            // Merge into the shared settings, replacing earlier values so later profiles win.
            props.forEach(merged::put);
        } catch (IOException e) {
            // Wrap I/O errors with the file name for context.
            throw new FrameworkException("Unable to read '" + resource + "'", e);
        }
    }

    /**
     * Checks that a string is neither null nor blank.
     *
     * @param value the string to check
     * @return true if it contains non-whitespace text
     */
    private static boolean isPresent(String value) {
        // Null and whitespace-only values both count as "not set".
        return value != null && !value.isBlank();
    }

    /**
     * Returns the trimmed value, or a fallback when it is null or blank.
     *
     * @param value    the candidate value
     * @param fallback the value to use when the candidate is absent
     * @return the trimmed value or the fallback
     */
    private static String blankToDefault(String value, String fallback) {
        // Prefer the supplied value when it has content.
        return isPresent(value) ? value.trim() : fallback;
    }
}
