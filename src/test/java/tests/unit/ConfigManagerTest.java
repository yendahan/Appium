package tests.unit;

import config.ConfigManager;
import exceptions.FrameworkException;
import org.testng.annotations.AfterMethod;
import org.testng.annotations.Test;

import java.time.Duration;

import static org.testng.Assert.assertEquals;
import static org.testng.Assert.assertFalse;
import static org.testng.Assert.assertThrows;
import static org.testng.Assert.assertTrue;

/**
 * Device-free tests for ConfigManager: profile loading, system-property overrides and value parsing.
 * Side effects: tests set JVM system properties; clearOverrides() resets them after each test.
 */
// Class-level @Test puts every public method in the "unit" group, which is the default for `mvn test`.
@Test(groups = "unit")
public class ConfigManagerTest {

    /**
     * Removes system properties set by the tests so they cannot leak into other tests.
     * Side effects: clears wait.explicit.seconds and appium.url from the JVM.
     */
    // alwaysRun makes cleanup happen even when the test failed.
    @AfterMethod(alwaysRun = true)
    public void clearOverrides() {
        // Reset the timeout override.
        System.clearProperty("wait.explicit.seconds");
        // Reset the Appium URL override.
        System.clearProperty("appium.url");
    }

    /**
     * Scenario: load the qa env with the emulator device profile.
     * Assertion: defaults and profile values (URL, device name, 15s explicit wait) are returned.
     */
    public void loadsDefaultsAndProfiles() {
        // Load the qa + emulator profiles.
        ConfigManager cfg = new ConfigManager("qa", "emulator");
        // Default Appium server URL.
        assertEquals(cfg.get("appium.url"), "http://127.0.0.1:4723");
        // Device name from the emulator profile.
        assertEquals(cfg.get("device.name"), "Android Emulator");
        // Seconds value is exposed as a Duration.
        assertEquals(cfg.getSeconds("wait.explicit.seconds"), Duration.ofSeconds(15));
    }

    /**
     * Scenario: blank or null env/device names.
     * Assertion: they fall back to the defaults qa and emulator.
     */
    public void blankProfilesFallBackToDefaults() {
        // Blank env and null device must not fail.
        ConfigManager cfg = new ConfigManager("  ", null);
        // Env falls back to qa.
        assertEquals(cfg.env(), "qa");
        // Device falls back to emulator.
        assertEquals(cfg.device(), "emulator");
    }

    /**
     * Scenario: a JVM system property is set for a key that also exists in the config files.
     * Assertion: the system property wins (this is how -D flags override config).
     * Side effects: sets appium.url; cleared by clearOverrides().
     */
    public void systemPropertyOverridesFile() {
        // Simulate -Dappium.url=... on the command line.
        System.setProperty("appium.url", "http://10.0.0.5:4723");
        // The override must beat the value from the physical profile.
        assertEquals(new ConfigManager("qa", "physical").get("appium.url"), "http://10.0.0.5:4723");
    }

    /**
     * Scenario: read an optional key that is not configured.
     * Assertion: get() returns an empty string (not null) and has() is false.
     */
    public void unsetOptionalValueIsEmptyNotNull() {
        // Load a valid profile.
        ConfigManager cfg = new ConfigManager("qa", "emulator");
        // Missing optional keys are empty so callers avoid null checks.
        assertEquals(cfg.get("does.not.exist"), "");
        // has() lets callers distinguish unset from empty.
        assertFalse(cfg.has("does.not.exist"));
    }

    /**
     * Scenario: require() on a missing key.
     * Assertion: fails fast with a message naming both the property key and its env-var form.
     */
    public void requireFailsFastWithKeyInMessage() {
        // Capture the exception so its message can be inspected.
        FrameworkException e = expectThrows(() -> new ConfigManager("qa", "emulator").require("does.not.exist"));
        // Message names the property key.
        assertTrue(e.getMessage().contains("does.not.exist"));
        // Message also names the env-var equivalent so users know how to set it.
        assertTrue(e.getMessage().contains("DOES_NOT_EXIST"));
    }

    /**
     * Scenario: construct with an unknown env or unknown device profile.
     * Assertion: FrameworkException in both cases.
     */
    public void unknownProfileIsRejected() {
        // Unknown env, valid device.
        assertThrows(FrameworkException.class, () -> new ConfigManager("nope", "emulator"));
        // Valid env, unknown device.
        assertThrows(FrameworkException.class, () -> new ConfigManager("qa", "nope"));
    }

    /**
     * Scenario: an integer setting contains non-numeric text.
     * Assertion: getInt throws FrameworkException instead of a raw NumberFormatException.
     * Side effects: sets wait.explicit.seconds; cleared by clearOverrides().
     */
    public void nonNumericIntegerIsRejected() {
        // Inject an invalid number through the override mechanism.
        System.setProperty("wait.explicit.seconds", "abc");
        // Parsing must fail with the framework's own exception type.
        assertThrows(FrameworkException.class, () -> new ConfigManager("qa", "emulator").getInt("wait.explicit.seconds"));
    }

    /**
     * Scenario: timeout values at and around the lower boundary.
     * Assertion: 0 and negative values are rejected; 1 second is the smallest accepted value.
     * Side effects: sets wait.explicit.seconds; cleared by clearOverrides().
     */
    public void zeroAndNegativeTimeoutsAreRejected() {
        // One manager is reused; overrides are read at call time.
        ConfigManager cfg = new ConfigManager("qa", "emulator");
        // Zero would mean no wait at all.
        System.setProperty("wait.explicit.seconds", "0");
        assertThrows(FrameworkException.class, () -> cfg.getSeconds("wait.explicit.seconds"));
        // Negative durations make no sense for waits.
        System.setProperty("wait.explicit.seconds", "-5");
        assertThrows(FrameworkException.class, () -> cfg.getSeconds("wait.explicit.seconds"));
        System.setProperty("wait.explicit.seconds", "1"); // smallest valid boundary
        // 1 second must be accepted and returned as a Duration.
        assertEquals(cfg.getSeconds("wait.explicit.seconds"), Duration.ofSeconds(1));
    }

    /**
     * Scenario: boolean settings from config and an invalid boolean text.
     * Assertion: configured values parse correctly; "maybe" is rejected.
     * Side effects: sets app.noReset temporarily; cleared in the finally block.
     */
    public void booleanParsing() {
        // Load a valid profile.
        ConfigManager cfg = new ConfigManager("qa", "emulator");
        // Permissions are auto-granted by default.
        assertTrue(cfg.getBoolean("app.autoGrantPermissions"));
        // The app is reset between sessions by default.
        assertFalse(cfg.getBoolean("app.noReset"));
        // Inject a value that is not true/false.
        System.setProperty("app.noReset", "maybe");
        try {
            // Anything other than a clear boolean must be rejected.
            assertThrows(FrameworkException.class, () -> cfg.getBoolean("app.noReset"));
        } finally {
            // Always remove the bad value so later tests are unaffected.
            System.clearProperty("app.noReset");
        }
    }

    /**
     * Runs code that is expected to throw and returns the exception for further assertions.
     *
     * @param r code expected to throw FrameworkException
     * @return the FrameworkException thrown by r
     * @throws AssertionError if r completes without throwing
     */
    private static FrameworkException expectThrows(Runnable r) {
        try {
            // Run the code under test.
            r.run();
        } catch (FrameworkException e) {
            // Hand the exception back so the caller can check its message.
            return e;
        }
        // Reaching here means nothing was thrown, which is a test failure.
        throw new AssertionError("Expected FrameworkException");
    }
}
