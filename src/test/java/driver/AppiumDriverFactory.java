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

    /** Utility class; not instantiable. */
    private AppiumDriverFactory() {
    }

    /**
     * Creates a new Android session on the configured Appium server.
     * Side effects: contacts the Appium server, launches the app on the device/emulator and disables implicit waits.
     *
     * @param cfg the configuration supplying server URL, device and app settings
     * @return a ready-to-use {@link AndroidDriver}
     * @throws FrameworkException if the server is unreachable, the URL is invalid or the session cannot be created
     */
    public static AndroidDriver create(ConfigManager cfg) {
        // Translate configuration into UiAutomator2 capabilities.
        UiAutomator2Options options = buildOptions(cfg);
        // Resolve the Appium server address from configuration.
        URL serverUrl = serverUrl(cfg);
        // Log the target so failed runs show which server/profile was used.
        LOG.info("Creating Android session on {} (env={}, device={})", serverUrl, cfg.env(), cfg.device());
        try {
            // Open the session; this is the call that actually starts the app on the device.
            AndroidDriver driver = new AndroidDriver(serverUrl, options);
            // Zero implicit wait so only MobileActions' explicit waits control timing (mixing them causes flakiness).
            driver.manage().timeouts().implicitlyWait(Duration.ZERO); // explicit waits only
            // Hand the live session to the caller.
            return driver;
        } catch (SessionNotCreatedException e) {
            // Server was reached but refused the session: point at the usual device/driver causes.
            throw new FrameworkException("Appium could not create a session. Check that the device/emulator is "
                    + "online (`adb devices`), the UiAutomator2 driver is installed, and the app settings are "
                    + "correct. Server said: " + e.getMessage(), e);
        } catch (RuntimeException e) {
            // Anything else is most likely a connection problem, so suggest checking the server.
            throw new FrameworkException("Could not reach Appium server at " + serverUrl
                    + ". Is it running? (" + e.getMessage() + ")", e);
        }
    }

    /**
     * Builds UiAutomator2 options from configuration.
     *
     * @param cfg the configuration to read device and app settings from
     * @return populated options; optional fields (udid, avd, platform version) are set only when configured
     * @throws FrameworkException if required settings are missing or the app under test is not configured
     */
    static UiAutomator2Options buildOptions(ConfigManager cfg) {
        // Start with the settings every session needs; require() fails fast if device.name is absent.
        UiAutomator2Options options = new UiAutomator2Options()
                .setDeviceName(cfg.require("device.name"))
                .setNewCommandTimeout(cfg.getSeconds("session.newCommandTimeout.seconds"))
                .setNoReset(cfg.getBoolean("app.noReset"))
                .setAutoGrantPermissions(cfg.getBoolean("app.autoGrantPermissions"));

        // Pin a specific device only when configured (needed when several are attached).
        if (cfg.has("device.udid")) {
            // Target the exact device by its serial/UDID.
            options.setUdid(cfg.get("device.udid"));
        }
        // Let Appium boot a named emulator image when configured.
        if (cfg.has("device.avd")) {
            // Name of the AVD to launch.
            options.setAvd(cfg.get("device.avd"));
        }
        // Pass the Android version only when set, otherwise Appium detects it.
        if (cfg.has("device.platformVersion")) {
            // Helps Appium choose the right driver behaviour for this OS version.
            options.setPlatformVersion(cfg.get("device.platformVersion"));
        }

        // Prefer installing an APK when a path is given.
        if (cfg.has("app.path")) {
            // Appium installs and launches this APK.
            options.setApp(cfg.get("app.path"));
        } else if (cfg.has("app.package") && cfg.has("app.activity")) {
            // Otherwise launch an app that is already installed, identified by package and activity.
            options.setAppPackage(cfg.get("app.package")).setAppActivity(cfg.get("app.activity"));
        } else {
            // Neither form is configured, so there is nothing to launch.
            throw new FrameworkException("App under test is not configured. Set app.path (APK) or both "
                    + "app.package and app.activity for env '" + cfg.env() + "'.");
        }
        // Return the finished options for session creation.
        return options;
    }

    /**
     * Reads and validates the Appium server URL from configuration.
     *
     * @param cfg the configuration holding {@code appium.url}
     * @return the parsed server URL
     * @throws FrameworkException if the setting is missing or not a valid URL
     */
    private static URL serverUrl(ConfigManager cfg) {
        // Required setting: fails with an actionable message if missing.
        String raw = cfg.require("appium.url");
        try {
            // Parse via URI first because it validates syntax more strictly than new URL(String).
            return URI.create(raw).toURL();
        } catch (MalformedURLException | IllegalArgumentException e) {
            // Echo the bad value so the typo is easy to spot.
            throw new FrameworkException("Invalid appium.url '" + raw + "'", e);
        }
    }
}
