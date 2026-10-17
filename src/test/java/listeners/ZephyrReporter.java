package listeners;

import config.ConfigManager;
import integrations.ZephyrClient;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.testng.ITestListener;
import org.testng.ITestResult;

import java.nio.file.Path;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;

/**
 * Publishes results of {@link ZephyrCase}-annotated tests to a Zephyr Scale test cycle.
 * Inactive unless env var {@code ZEPHYR_TOKEN} and {@code zephyr.project.key} (or {@code ZEPHYR_PROJECT_KEY}) are set.
 * Errors are only logged so Jira problems never change a test result.
 */
public class ZephyrReporter implements ITestListener {

    private static final Logger LOG = LoggerFactory.getLogger(ZephyrReporter.class);
    private static final String DEFAULT_URL = "https://api.zephyrscale.smartbear.com/v2";

    private static ZephyrClient client;
    private static String cycleKey;
    private static boolean initialised;
    /** Case key to execution key in the current cycle; lets a result update the pre-created row instead of adding one. */
    private static final java.util.Map<String, String> EXECUTIONS = new java.util.HashMap<>();

    @Override
    public void onTestSuccess(ITestResult r) {
        publish(r, "Pass");
    }

    @Override
    public void onTestFailure(ITestResult r) {
        publish(r, "Fail");
    }

    @Override
    public void onTestSkipped(ITestResult r) {
        publish(r, "Blocked");
    }

    private static synchronized void publish(ITestResult r, String status) {
        ZephyrCase tc = r.getMethod().getConstructorOrMethod().getMethod().getAnnotation(ZephyrCase.class);
        if (tc == null || !init()) {
            return;
        }
        // Comment keeps only the failure text; the screenshot goes into the step actual result.
        String comment = r.getThrowable() == null ? null : "Actual: " + r.getThrowable();
        String actual = r.getThrowable() == null ? "As expected" : String.valueOf(r.getThrowable());
        String screenshot = null;
        Object shot = r.getAttribute(TestListener.SCREENSHOT_ATTR);
        if (shot instanceof Path p) {
            // Local path (e.g. inside a synced OneDrive folder); only openable on the machine that ran the tests.
            screenshot = "Screenshot: " + p.toAbsolutePath();
        }
        try {
            String execKey = EXECUTIONS.get(tc.value());
            if (execKey != null) {
                client.updateExecution(execKey, status, comment);
            } else {
                execKey = client.postExecution(cycleKey, tc.value(), status, comment);
                EXECUTIONS.put(tc.value(), execKey);
            }
            LOG.info("Zephyr: {} -> {} in {}", tc.value(), status, cycleKey);
            try {
                client.updateStepResults(execKey, status, actual, screenshot);
            } catch (Exception e) {
                LOG.warn("Zephyr: could not update step results for {}: {}", execKey, e.toString());
            }
        } catch (Exception e) {
            LOG.warn("Zephyr: could not publish {}: {}", tc.value(), e.toString());
        }
    }

    /**
     * Makes the cycle list every case of the configured folder (default "Mobile Automation") as Not Executed, so tests that
     * are not run this time (e.g. risky ones) still appear. Best-effort: failures are only logged.
     */
    private static void prepareCycle(ZephyrClient c, ConfigManager cfg) {
        try {
            String folder = cfg.has("zephyr.cases.folder") ? cfg.get("zephyr.cases.folder") : "Mobile Automation";
            EXECUTIONS.putAll(c.latestExecutions(cycleKey));
            for (String caseKey : c.caseKeysInFolder(folder)) {
                String exec = EXECUTIONS.get(caseKey);
                if (exec == null) {
                    EXECUTIONS.put(caseKey, c.postExecution(cycleKey, caseKey, "Not Executed", null));
                } else {
                    c.updateExecution(exec, "Not Executed", null);
                }
            }
            LOG.info("Zephyr: cycle {} lists {} cases", cycleKey, EXECUTIONS.size());
        } catch (Exception e) {
            LOG.warn("Zephyr: could not pre-fill cycle {}: {}", cycleKey, e.toString());
        }
    }

    /** Lazily creates the client and this run's cycle once; returns false when Zephyr is not configured or setup failed. */
    private static boolean init() {
        if (initialised) {
            return client != null;
        }
        initialised = true;
        String token = System.getenv("ZEPHYR_TOKEN");
        ConfigManager cfg = ConfigManager.get();
        if (token == null || token.isBlank() || !cfg.has("zephyr.project.key")) {
            return false;
        }
        try {
            String url = cfg.has("zephyr.base.url") ? cfg.get("zephyr.base.url") : DEFAULT_URL;
            ZephyrClient c = new ZephyrClient(url, token, cfg.get("zephyr.project.key"));
            String reuse = System.getenv("ZEPHYR_CYCLE_KEY");
            if (reuse == null || reuse.isBlank()) {
                reuse = cfg.has("zephyr.cycle.key") ? cfg.get("zephyr.cycle.key") : null;
            }
            if (reuse != null && !reuse.isBlank()) {
                cycleKey = reuse.trim();
                LOG.info("Zephyr: reusing cycle {}", cycleKey);
            } else {
                String stamp = LocalDateTime.now().format(DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm"));
                cycleKey = c.createCycle("Automation " + cfg.env() + "/" + cfg.device() + " " + stamp);
                LOG.info("Zephyr: created cycle {}", cycleKey);
            }
            client = c;
            prepareCycle(c, cfg);
            return true;
        } catch (Exception e) {
            LOG.warn("Zephyr disabled for this run: {}", e.toString());
            return false;
        }
    }
}
