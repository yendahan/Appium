package tests.unit;

import com.fasterxml.jackson.databind.JsonNode;
import data.TestDataLoader;
import exceptions.FrameworkException;
import org.openqa.selenium.By;
import org.testng.annotations.DataProvider;
import org.testng.annotations.Test;
import utils.LocatorParser;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;

import static org.testng.Assert.assertEquals;
import static org.testng.Assert.assertNotNull;
import static org.testng.Assert.assertThrows;
import static org.testng.Assert.assertTrue;

/**
 * Device-free tests for LocatorParser, which turns "strategy=value" strings into Selenium By objects.
 * Valid and invalid samples come from the qa test data file.
 * Side effects: none.
 */
// Class-level @Test puts every public method in the "unit" group, which is the default for `mvn test`.
@Test(groups = "unit")
public class LocatorParserTest {

    // Loads the qa test data file once for both data providers.
    private static final TestDataLoader DATA = new TestDataLoader("qa");

    /**
     * Supplies the valid locator samples.
     *
     * @return rows of {raw locator string, strategy name} read from the validLocators node
     */
    // Feeds parsesSupportedStrategies.
    @DataProvider(name = "valid")
    public Object[][] valid() {
        // Collect rows dynamically because the sample count depends on the data file.
        List<Object[]> rows = new ArrayList<>();
        // Each entry maps a strategy name (key) to a raw locator (value).
        for (Map.Entry<String, JsonNode> e : DATA.node("validLocators").properties()) {
            // Key is the strategy name, value is the raw locator text.
            rows.add(new Object[]{e.getKey(), e.getValue().asText()});
        }
        // Convert to the array shape TestNG expects.
        return rows.toArray(new Object[0][]);
    }

    /**
     * Supplies malformed locator samples.
     *
     * @return single-column rows from the invalidLocators node, plus a null row
     */
    // Feeds rejectsMalformedLocators.
    @DataProvider(name = "invalid")
    public Object[][] invalid() {
        // Collect rows dynamically because the sample count depends on the data file.
        List<Object[]> rows = new ArrayList<>();
        // One row per malformed string in the data file.
        DATA.node("invalidLocators").forEach(n -> rows.add(new Object[]{n.asText()}));
        // Null is also invalid input and must be handled gracefully.
        rows.add(new Object[]{null});
        // Convert to the array shape TestNG expects.
        return rows.toArray(new Object[0][]);
    }

    /**
     * Scenario: each supported locator strategy.
     * Assertion: parse returns a non-null By with a non-empty description.
     *
     * @param raw      locator string such as "id=..." from the data file
     * @param strategy strategy name, used only in the failure message
     */
    // Runs once per valid sample.
    @Test(dataProvider = "valid")
    public void parsesSupportedStrategies(String raw, String strategy) {
        // Parse the raw string into a Selenium By.
        By by = LocatorParser.parse(raw);
        // Parsing must produce a locator object.
        assertNotNull(by);
        // The By should describe itself; the strategy name helps identify the failing sample.
        assertTrue(by.toString().length() > 0, "strategy " + strategy);
    }

    /**
     * Scenario: malformed or null locator strings.
     * Assertion: parse throws FrameworkException.
     *
     * @param raw an invalid locator string, or null
     */
    // Runs once per invalid sample.
    @Test(dataProvider = "invalid")
    public void rejectsMalformedLocators(String raw) {
        // Bad locators must fail with the framework's own exception, not a generic one.
        assertThrows(FrameworkException.class, () -> LocatorParser.parse(raw));
    }

    /**
     * Scenario: the locator value itself contains '='.
     * Assertion: only the first '=' splits strategy from value, so "a=b" stays in the parsed locator.
     */
    public void valueMayContainEqualsSign() {
        // Splitting on every '=' would truncate the XPath; the full text must survive.
        assertTrue(LocatorParser.parse("xpath=//*[@text='a=b']").toString().contains("a=b"));
    }

    /**
     * Scenario: text with double quotes and a backslash is embedded in a UiAutomator selector.
     * Assertion: quotes and backslashes are escaped with a leading backslash.
     */
    public void escapesQuotesAndBackslashesForUiSelector() {
        // Unescaped quotes would break out of the UiSelector string literal.
        assertEquals(LocatorParser.escapeUiSelector("say \"hi\"\\"), "say \\\"hi\\\"\\\\");
    }
}
