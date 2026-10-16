package driver;

import io.appium.java_client.android.AndroidDriver;

/** Thread-safe holder so tests can run in parallel with one session each. */
public final class DriverManager {

    private static final ThreadLocal<AndroidDriver> DRIVER = new ThreadLocal<>();

    /** Utility class; not instantiable. */
    private DriverManager() {
    }

    /**
     * Returns the driver bound to the calling thread.
     *
     * @return the current thread's driver, or null if no session has been set
     */
    public static AndroidDriver get() {
        // Read the per-thread slot so parallel tests never see each other's sessions.
        return DRIVER.get();
    }

    /**
     * Binds a driver to the calling thread.
     * Side effect: replaces any driver previously stored for this thread (without quitting it).
     *
     * @param driver the session to store for this thread
     */
    public static void set(AndroidDriver driver) {
        // Store the session in the per-thread slot for later retrieval by tests and listeners.
        DRIVER.set(driver);
    }

    /**
     * Quits the calling thread's session (if any) and clears the thread slot.
     * Side effect: ends the Appium session on the server; safe to call when no driver is set.
     */
    public static void quit() {
        // Grab the current thread's driver so we can shut it down.
        AndroidDriver driver = DRIVER.get();
        try {
            // Only quit when a session exists; quit() on null would throw.
            if (driver != null) {
                // Release the device/emulator session on the Appium server.
                driver.quit();
            }
        } finally {
            // Always clear the ThreadLocal so pooled threads do not leak a dead driver.
            DRIVER.remove();
        }
    }
}
