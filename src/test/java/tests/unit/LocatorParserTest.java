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

@Test(groups = "unit")
public class LocatorParserTest {

    private static final TestDataLoader DATA = new TestDataLoader("qa");

    @DataProvider(name = "valid")
    public Object[][] valid() {
        List<Object[]> rows = new ArrayList<>();
        for (Map.Entry<String, JsonNode> e : DATA.node("validLocators").properties()) {
            rows.add(new Object[]{e.getKey(), e.getValue().asText()});
        }
        return rows.toArray(new Object[0][]);
    }

    @DataProvider(name = "invalid")
    public Object[][] invalid() {
        List<Object[]> rows = new ArrayList<>();
        DATA.node("invalidLocators").forEach(n -> rows.add(new Object[]{n.asText()}));
        rows.add(new Object[]{null});
        return rows.toArray(new Object[0][]);
    }

    @Test(dataProvider = "valid")
    public void parsesSupportedStrategies(String raw, String strategy) {
        By by = LocatorParser.parse(raw);
        assertNotNull(by);
        assertTrue(by.toString().length() > 0, "strategy " + strategy);
    }

    @Test(dataProvider = "invalid")
    public void rejectsMalformedLocators(String raw) {
        assertThrows(FrameworkException.class, () -> LocatorParser.parse(raw));
    }

    public void valueMayContainEqualsSign() {
        assertTrue(LocatorParser.parse("xpath=//*[@text='a=b']").toString().contains("a=b"));
    }

    public void escapesQuotesAndBackslashesForUiSelector() {
        assertEquals(LocatorParser.escapeUiSelector("say \"hi\"\\"), "say \\\"hi\\\"\\\\");
    }
}
