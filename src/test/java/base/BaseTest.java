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

    @BeforeMethod(alwaysRun = true)
    public void startSession(Method method) {
        log.info("=== START {}.{} ===", getClass().getSimpleName(), method.getName());
        DriverManager.set(AppiumDriverFactory.create(ConfigManager.get()));
    }

    @AfterMethod(alwaysRun = true)
    public void stopSession(Method method) {
        log.info("=== END {}.{} ===", getClass().getSimpleName(), method.getName());
        DriverManager.quit();
    }

    protected AndroidDriver driver() {
        return DriverManager.get();
    }
}
