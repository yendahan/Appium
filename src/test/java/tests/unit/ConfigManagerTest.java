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

@Test(groups = "unit")
public class ConfigManagerTest {

    @AfterMethod(alwaysRun = true)
    public void clearOverrides() {
        System.clearProperty("wait.explicit.seconds");
        System.clearProperty("appium.url");
    }

    public void loadsDefaultsAndProfiles() {
        ConfigManager cfg = new ConfigManager("qa", "emulator");
        assertEquals(cfg.get("appium.url"), "http://127.0.0.1:4723");
        assertEquals(cfg.get("device.name"), "Android Emulator");
        assertEquals(cfg.getSeconds("wait.explicit.seconds"), Duration.ofSeconds(15));
    }

    public void blankProfilesFallBackToDefaults() {
        ConfigManager cfg = new ConfigManager("  ", null);
        assertEquals(cfg.env(), "qa");
        assertEquals(cfg.device(), "emulator");
    }

    public void systemPropertyOverridesFile() {
        System.setProperty("appium.url", "http://10.0.0.5:4723");
        assertEquals(new ConfigManager("qa", "physical").get("appium.url"), "http://10.0.0.5:4723");
    }

    public void unsetOptionalValueIsEmptyNotNull() {
        ConfigManager cfg = new ConfigManager("qa", "emulator");
        assertEquals(cfg.get("does.not.exist"), "");
        assertFalse(cfg.has("does.not.exist"));
    }

    public void requireFailsFastWithKeyInMessage() {
        FrameworkException e = expectThrows(() -> new ConfigManager("qa", "emulator").require("does.not.exist"));
        assertTrue(e.getMessage().contains("does.not.exist"));
        assertTrue(e.getMessage().contains("DOES_NOT_EXIST"));
    }

    public void unknownProfileIsRejected() {
        assertThrows(FrameworkException.class, () -> new ConfigManager("nope", "emulator"));
        assertThrows(FrameworkException.class, () -> new ConfigManager("qa", "nope"));
    }

    public void nonNumericIntegerIsRejected() {
        System.setProperty("wait.explicit.seconds", "abc");
        assertThrows(FrameworkException.class, () -> new ConfigManager("qa", "emulator").getInt("wait.explicit.seconds"));
    }

    public void zeroAndNegativeTimeoutsAreRejected() {
        ConfigManager cfg = new ConfigManager("qa", "emulator");
        System.setProperty("wait.explicit.seconds", "0");
        assertThrows(FrameworkException.class, () -> cfg.getSeconds("wait.explicit.seconds"));
        System.setProperty("wait.explicit.seconds", "-5");
        assertThrows(FrameworkException.class, () -> cfg.getSeconds("wait.explicit.seconds"));
        System.setProperty("wait.explicit.seconds", "1"); // smallest valid boundary
        assertEquals(cfg.getSeconds("wait.explicit.seconds"), Duration.ofSeconds(1));
    }

    public void booleanParsing() {
        ConfigManager cfg = new ConfigManager("qa", "emulator");
        assertTrue(cfg.getBoolean("app.autoGrantPermissions"));
        assertFalse(cfg.getBoolean("app.noReset"));
        System.setProperty("app.noReset", "maybe");
        try {
            assertThrows(FrameworkException.class, () -> cfg.getBoolean("app.noReset"));
        } finally {
            System.clearProperty("app.noReset");
        }
    }

    private static FrameworkException expectThrows(Runnable r) {
        try {
            r.run();
        } catch (FrameworkException e) {
            return e;
        }
        throw new AssertionError("Expected FrameworkException");
    }
}
