package base;

import config.ConfigManager;
import driver.AppiumDriverFactory;
import driver.DriverManager;
import io.appium.java_client.android.AndroidDriver;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import listeners.TestListener;
import org.testng.annotations.AfterMethod;
import org.testng.annotations.BeforeMethod;
import org.testng.annotations.Listeners;

import java.lang.reflect.Method;

/** Creates a fresh Android session before every test method and always quits it afterwards. */
@Listeners(TestListener.class)
public abstract class BaseTest {

    protected final Logger log = LoggerFactory.getLogger(getClass());

    /**
     * Starts a new Appium session before each test method.
     * Side effects: launches the app on the device and stores the driver in {@link DriverManager}.
     *
     * @param method the test method about to run (used for log output)
     */
    @BeforeMethod(alwaysRun = true)
    public void startSession(Method method) {
        // Log a clear boundary so each test is easy to find in the console output.
        log.info("=== START {}.{} ===", getClass().getSimpleName(), method.getName());
        // Create the session from config and bind it to this thread for tests and listeners.
        DriverManager.set(AppiumDriverFactory.create(ConfigManager.get()));
    }

    /**
     * Ends the Appium session after each test method, even if the test failed.
     * Side effect: quits the driver and clears the thread-local holder.
     *
     * @param method the test method that just ran (used for log output)
     */
    @AfterMethod(alwaysRun = true)
    public void stopSession(Method method) {
        // Log the end boundary matching the START line.
        log.info("=== END {}.{} ===", getClass().getSimpleName(), method.getName());
        // Quit and clear the driver so the next test starts from a clean session.
        DriverManager.quit();
    }

    /**
     * Gives subclasses access to the current test's driver.
     *
     * @return the driver bound to the current thread
     */
    protected AndroidDriver driver() {
        // Delegate to the thread-local holder so parallel tests stay isolated.
        return DriverManager.get();
    }
}
