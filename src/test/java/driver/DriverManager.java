package driver;

import io.appium.java_client.android.AndroidDriver;

/** Thread-safe holder so tests can run in parallel with one session each. */
public final class DriverManager {

    private static final ThreadLocal<AndroidDriver> DRIVER = new ThreadLocal<>();

    private DriverManager() {
    }

    public static AndroidDriver get() {
        return DRIVER.get();
    }

    public static void set(AndroidDriver driver) {
        DRIVER.set(driver);
    }

    public static void quit() {
        AndroidDriver driver = DRIVER.get();
        try {
            if (driver != null) {
                driver.quit();
            }
        } finally {
            DRIVER.remove();
        }
    }
}
