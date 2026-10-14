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

    private static final class Holder {
        static final ConfigManager INSTANCE = new ConfigManager(
                System.getProperty("env", DEFAULT_ENV), System.getProperty("device", DEFAULT_DEVICE));
    }

    public static ConfigManager get() {
        return Holder.INSTANCE;
    }

    /** Visible for tests that need an isolated instance. */
    public ConfigManager(String env, String device) {
        this.env = blankToDefault(env, DEFAULT_ENV);
        this.device = blankToDefault(device, DEFAULT_DEVICE);
        load("config/default.properties");
        load("config/env/" + this.env + ".properties");
        load("config/devices/" + this.device + ".properties");
    }

    public String env() {
        return env;
    }

    public String device() {
        return device;
    }

    /** Returns the value, or empty string when not configured. */
    public String get(String key) {
        String override = System.getProperty(key);
        if (isPresent(override)) {
            return override.trim();
        }
        String fromEnv = System.getenv(toEnvName(key));
        if (isPresent(fromEnv)) {
            return fromEnv.trim();
        }
        return merged.getProperty(key, "").trim();
    }

    public boolean has(String key) {
        return !get(key).isEmpty();
    }

    /** Returns the value or fails fast with an actionable message. */
    public String require(String key) {
        String value = get(key);
        if (value.isEmpty()) {
            throw new FrameworkException("Missing required config '" + key + "'. Set it in config/env/" + env
                    + ".properties, config/devices/" + device + ".properties, via -D" + key + "=..., or env var "
                    + toEnvName(key) + ".");
        }
        return value;
    }

    public int getInt(String key) {
        String value = require(key);
        try {
            return Integer.parseInt(value);
        } catch (NumberFormatException e) {
            throw new FrameworkException("Config '" + key + "' must be an integer but was '" + value + "'", e);
        }
    }

    public double getDouble(String key) {
        String value = require(key);
        try {
            return Double.parseDouble(value);
        } catch (NumberFormatException e) {
            throw new FrameworkException("Config '" + key + "' must be a number but was '" + value + "'", e);
        }
    }

    public boolean getBoolean(String key) {
        String value = get(key);
        if (value.isEmpty() || value.equalsIgnoreCase("false")) {
            return false;
        }
        if (value.equalsIgnoreCase("true")) {
            return true;
        }
        throw new FrameworkException("Config '" + key + "' must be true or false but was '" + value + "'");
    }

    public Duration getSeconds(String key) {
        int seconds = getInt(key);
        if (seconds <= 0) {
            throw new FrameworkException("Config '" + key + "' must be > 0 but was " + seconds);
        }
        return Duration.ofSeconds(seconds);
    }

    static String toEnvName(String key) {
        return key.toUpperCase().replace('.', '_');
    }

    private void load(String resource) {
        try (InputStream in = Thread.currentThread().getContextClassLoader().getResourceAsStream(resource)) {
            if (in == null) {
                throw new FrameworkException("Config resource '" + resource
                        + "' not found on classpath (unknown -Denv or -Ddevice profile?)");
            }
            Properties props = new Properties();
            props.load(in);
            props.forEach(merged::put);
        } catch (IOException e) {
            throw new FrameworkException("Unable to read '" + resource + "'", e);
        }
    }

    private static boolean isPresent(String value) {
        return value != null && !value.isBlank();
    }

    private static String blankToDefault(String value, String fallback) {
        return isPresent(value) ? value.trim() : fallback;
    }
}
