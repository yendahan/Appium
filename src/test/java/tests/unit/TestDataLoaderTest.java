package tests.unit;

import com.fasterxml.jackson.databind.JsonNode;
import data.TestDataLoader;
import exceptions.FrameworkException;
import org.testng.annotations.Test;

import java.util.Map;

import static org.testng.Assert.assertEquals;
import static org.testng.Assert.assertThrows;
import static org.testng.Assert.expectThrows;

@Test(groups = "unit")
public class TestDataLoaderTest {

    public void resolvesEnvPlaceholders() {
        Map<String, String> fake = Map.of("TEST_USERNAME", "alice", "TEST_PASSWORD", "s3cr=t$1");
        JsonNode creds = new TestDataLoader("qa").node("credentials", fake::get);
        assertEquals(creds.get("username").asText(), "alice");
        assertEquals(creds.get("password").asText(), "s3cr=t$1"); // regex-special chars survive
    }

    public void missingEnvVarFailsWithVariableName() {
        FrameworkException e = expectThrows(FrameworkException.class,
                () -> new TestDataLoader("qa").node("credentials", k -> null));
        assertEquals(e.getMessage().contains("TEST_USERNAME"), true);
    }

    public void emptyEnvVarIsTreatedAsMissing() {
        assertThrows(FrameworkException.class, () -> new TestDataLoader("qa").node("credentials", k -> ""));
    }

    public void unknownKeyAndUnknownEnvAreRejected() {
        assertThrows(FrameworkException.class, () -> new TestDataLoader("qa").node("nope"));
        assertThrows(FrameworkException.class, () -> new TestDataLoader("nonexistent-env"));
    }

    public void nodesWithoutPlaceholdersNeedNoEnvironment() {
        assertEquals(new TestDataLoader("qa").node("invalidLocators", k -> null).size(), 5);
    }
}
