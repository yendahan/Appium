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

    /**
     * Captures a PASSED screenshot and links it from the TestNG report.
     * Side effects: writes a PNG under the artifacts directory and appends HTML to the report.
     *
     * @param result the TestNG result of the passed test
     */
    @Override
    public void onTestSuccess(ITestResult result) {
        // Look up this thread's session; the test has finished but the driver is still open.
        AndroidDriver driver = DriverManager.get();
        // Nothing to capture if no session exists (e.g. unit tests).
        if (driver == null) {
            return;
        }
        // Build a readable Class.method name used for the file name and report.
        String name = result.getTestClass().getRealClass().getSimpleName() + "." + result.getMethod().getMethodName();
        // Wrap in attempt() so a screenshot problem cannot turn a passing test into an error.
        attempt("screenshot", () -> {
            // Save the screenshot into the PASSED subfolder of this run.
            Path shot = new MobileActions(driver).screenshot("PASSED", name);
            // Embed a link and thumbnail in the HTML report (true also echoes to the console log).
            Reporter.log("<br/><a href=\"" + shot.toAbsolutePath().toUri() + "\">Screenshot</a><br/>"
                    + "<img src=\"" + shot.toAbsolutePath().toUri() + "\" height=\"300\"/>", true);
        });
    }

    /**
     * Captures diagnostics (screenshot, page source, logcat) for a failed test.
     * Side effects: writes files under the artifacts directory and appends links to the TestNG report.
     * Each capture is independent and errors are only logged, so the original failure is never masked.
     *
     * @param result the TestNG result of the failed test
     */
    @Override
    public void onTestFailure(ITestResult result) {
        // Look up this thread's session, which is still open at this point.
        AndroidDriver driver = DriverManager.get();
        // Build a readable Class.method name used for file names and logs.
        String name = result.getTestClass().getRealClass().getSimpleName() + "." + result.getMethod().getMethodName();
        // Log the failure cause first so it is visible even if diagnostics capture fails.
        LOG.error("FAILED {}: {}", name, String.valueOf(result.getThrowable()));
        // Without a session (e.g. it failed to start) there is nothing to capture.
        if (driver == null) {
            // Explain the skip so missing artifacts are not a mystery.
            LOG.warn("No driver session available; skipping diagnostics for {}", name);
            return;
        }
        // Reuse one actions helper for the screenshot and page source.
        MobileActions actions = new MobileActions(driver);
        // Capture the visible screen into the FAILED subfolder.
        attempt("screenshot", () -> {
            // Save the PNG for this failure.
            Path shot = actions.screenshot("FAILED", name);
            // Link and embed the image in the HTML report.
            Reporter.log("<br/><a href=\"" + shot.toAbsolutePath().toUri() + "\">Screenshot</a><br/>"
                    + "<img src=\"" + shot.toAbsolutePath().toUri() + "\" height=\"300\"/>", true);
        });
        // Save the UI hierarchy, which helps diagnose wrong or missing locators.
        attempt("page source", () -> save(name, "pagesource.xml", actions.pageSource()));
        // Save recent device logs, which help diagnose app crashes and network errors.
        attempt("logcat", () -> save(name, "logcat.txt", driver.manage().logs().get("logcat").getAll().stream()
                .map(LogEntry::toString).collect(Collectors.joining(System.lineSeparator()))));
    }

    /**
     * Writes diagnostic text to a file and links it from the report.
     * Side effects: creates the diagnostics directory, writes the file, appends to the report and logs the path.
     *
     * @param name    test name used as the file name prefix
     * @param suffix  file name suffix, also used as the link label
     * @param content text to write
     * @throws Exception if the directory or file cannot be written
     */
    private static void save(String name, String suffix, String content) throws Exception {
        // Resolve the diagnostics folder from the configured artifacts directory.
        Path dir = Paths.get(ConfigManager.get().require("artifacts.dir"), "diagnostics");
        // Ensure the folder exists before writing.
        Files.createDirectories(dir);
        // Name the file after the test so artifacts map back to failures.
        Path file = dir.resolve(name + "-" + suffix);
        // Persist the captured content.
        Files.writeString(file, content);
        // Add a clickable link to the HTML report.
        Reporter.log("<br/><a href=\"" + file.toAbsolutePath().toUri() + "\">" + suffix + "</a>", true);
        // Record the location in the console log as well.
        LOG.info("Saved diagnostics: {}", file);
    }

    /**
     * Runs a diagnostics step and swallows any failure so it cannot mask the test result.
     * Side effect: logs a warning when the step throws.
     *
     * @param what short description of the step, used in the warning
     * @param r    the step to run
     */
    private static void attempt(String what, ThrowingRunnable r) {
        try {
            // Execute the capture step.
            r.run();
        } catch (Exception e) {
            // Only log: diagnostics are best-effort and must not hide the original failure.
            LOG.warn("Could not capture {}: {}", what, e.toString());
        }
    }

    /** A runnable that may throw checked exceptions, so capture steps can be passed to {@code attempt}. */
    @FunctionalInterface
    private interface ThrowingRunnable {
        /**
         * Performs the action.
         *
         * @throws Exception on any failure; handled by the caller
         */
        void run() throws Exception;
    }
}
