package driver;

import config.ConfigManager;
import exceptions.FrameworkException;
import io.appium.java_client.android.AndroidDriver;
import io.appium.java_client.android.options.UiAutomator2Options;
import org.openqa.selenium.SessionNotCreatedException;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.net.MalformedURLException;
import java.net.URI;
import java.net.URL;
import java.time.Duration;

/** Builds {@link AndroidDriver} sessions (UiAutomator2) from configuration. Works for emulators and real devices. */
public final class AppiumDriverFactory {

    private static final Logger LOG = LoggerFactory.getLogger(AppiumDriverFactory.class);

    private AppiumDriverFactory() {
    }

    public static AndroidDriver create(ConfigManager cfg) {
        UiAutomator2Options options = buildOptions(cfg);
        URL serverUrl = serverUrl(cfg);
        LOG.info("Creating Android session on {} (env={}, device={})", serverUrl, cfg.env(), cfg.device());
        try {
            AndroidDriver driver = new AndroidDriver(serverUrl, options);
            driver.manage().timeouts().implicitlyWait(Duration.ZERO); // explicit waits only
            return driver;
        } catch (SessionNotCreatedException e) {
            throw new FrameworkException("Appium could not create a session. Check that the device/emulator is "
                    + "online (`adb devices`), the UiAutomator2 driver is installed, and the app settings are "
                    + "correct. Server said: " + e.getMessage(), e);
        } catch (RuntimeException e) {
            throw new FrameworkException("Could not reach Appium server at " + serverUrl
                    + ". Is it running? (" + e.getMessage() + ")", e);
        }
    }

    static UiAutomator2Options buildOptions(ConfigManager cfg) {
        UiAutomator2Options options = new UiAutomator2Options()
                .setDeviceName(cfg.require("device.name"))
                .setNewCommandTimeout(cfg.getSeconds("session.newCommandTimeout.seconds"))
                .setNoReset(cfg.getBoolean("app.noReset"))
                .setAutoGrantPermissions(cfg.getBoolean("app.autoGrantPermissions"));

        if (cfg.has("device.udid")) {
            options.setUdid(cfg.get("device.udid"));
        }
        if (cfg.has("device.avd")) {
            options.setAvd(cfg.get("device.avd"));
        }
        if (cfg.has("device.platformVersion")) {
            options.setPlatformVersion(cfg.get("device.platformVersion"));
        }

        if (cfg.has("app.path")) {
            options.setApp(cfg.get("app.path"));
        } else if (cfg.has("app.package") && cfg.has("app.activity")) {
            options.setAppPackage(cfg.get("app.package")).setAppActivity(cfg.get("app.activity"));
        } else {
            throw new FrameworkException("App under test is not configured. Set app.path (APK) or both "
                    + "app.package and app.activity for env '" + cfg.env() + "'.");
        }
        return options;
    }

    private static URL serverUrl(ConfigManager cfg) {
        String raw = cfg.require("appium.url");
        try {
            return URI.create(raw).toURL();
        } catch (MalformedURLException | IllegalArgumentException e) {
            throw new FrameworkException("Invalid appium.url '" + raw + "'", e);
        }
    }
}
