package listeners;

import actions.MobileActions;
import config.ConfigManager;
import driver.DriverManager;
import io.appium.java_client.android.AndroidDriver;
import org.openqa.selenium.logging.LogEntry;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.testng.ITestListener;
import org.testng.ITestResult;
import org.testng.Reporter;

import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.stream.Collectors;

/**
 * On success, saves a screenshot. On failure, saves a screenshot, the UI hierarchy (page source) and recent logcat output, and links them
 * from the TestNG HTML report. Diagnostics errors are logged and never mask the original failure.
 */
public class TestListener implements ITestListener {

    private static final Logger LOG = LoggerFactory.getLogger(TestListener.class);

    @Override
    public void onTestSuccess(ITestResult result) {
        AndroidDriver driver = DriverManager.get();
        if (driver == null) {
            return;
        }
        String name = result.getTestClass().getRealClass().getSimpleName() + "." + result.getMethod().getMethodName();
        attempt("screenshot", () -> {
            Path shot = new MobileActions(driver).screenshot("PASSED", name);
            Reporter.log("<br/><a href=\"" + shot.toAbsolutePath().toUri() + "\">Screenshot</a><br/>"
                    + "<img src=\"" + shot.toAbsolutePath().toUri() + "\" height=\"300\"/>", true);
        });
    }

    @Override
    public void onTestFailure(ITestResult result) {
        AndroidDriver driver = DriverManager.get();
        String name = result.getTestClass().getRealClass().getSimpleName() + "." + result.getMethod().getMethodName();
        LOG.error("FAILED {}: {}", name, String.valueOf(result.getThrowable()));
        if (driver == null) {
            LOG.warn("No driver session available; skipping diagnostics for {}", name);
            return;
        }
        MobileActions actions = new MobileActions(driver);
        attempt("screenshot", () -> {
            Path shot = actions.screenshot("FAILED", name);
            Reporter.log("<br/><a href=\"" + shot.toAbsolutePath().toUri() + "\">Screenshot</a><br/>"
                    + "<img src=\"" + shot.toAbsolutePath().toUri() + "\" height=\"300\"/>", true);
        });
        attempt("page source", () -> save(name, "pagesource.xml", actions.pageSource()));
        attempt("logcat", () -> save(name, "logcat.txt", driver.manage().logs().get("logcat").getAll().stream()
                .map(LogEntry::toString).collect(Collectors.joining(System.lineSeparator()))));
    }

    private static void save(String name, String suffix, String content) throws Exception {
        Path dir = Paths.get(ConfigManager.get().require("artifacts.dir"), "diagnostics");
        Files.createDirectories(dir);
        Path file = dir.resolve(name + "-" + suffix);
        Files.writeString(file, content);
        Reporter.log("<br/><a href=\"" + file.toAbsolutePath().toUri() + "\">" + suffix + "</a>", true);
        LOG.info("Saved diagnostics: {}", file);
    }

    private static void attempt(String what, ThrowingRunnable r) {
        try {
            r.run();
        } catch (Exception e) {
            LOG.warn("Could not capture {}: {}", what, e.toString());
        }
    }

    @FunctionalInterface
    private interface ThrowingRunnable {
        void run() throws Exception;
    }
}
