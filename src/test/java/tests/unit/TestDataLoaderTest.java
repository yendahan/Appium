package tests.unit;

import com.fasterxml.jackson.databind.JsonNode;
import data.TestDataLoader;
import exceptions.FrameworkException;
import org.testng.annotations.Test;

import java.util.Map;

import static org.testng.Assert.assertEquals;
import static org.testng.Assert.assertThrows;
import static org.testng.Assert.expectThrows;

/**
 * Device-free tests for TestDataLoader: JSON test data loading and env-var placeholder resolution.
 * Uses fake environment lookups, so no real credentials are read or written.
 * Side effects: none.
 */
// Class-level @Test puts every public method in the "unit" group, which is the default for `mvn test`.
@Test(groups = "unit")
public class TestDataLoaderTest {

    /**
     * Scenario: credentials contain placeholders for environment variables.
     * Assertion: they are replaced with the supplied values, including regex-special characters.
     */
    public void resolvesEnvPlaceholders() {
        // Fake environment so the test never touches real credentials.
        Map<String, String> fake = Map.of("TEST_USERNAME", "alice", "TEST_PASSWORD", "s3cr=t$1");
        // Load the credentials node using the fake lookup instead of System.getenv.
        JsonNode creds = new TestDataLoader("qa").node("credentials", fake::get);
        // Username placeholder is replaced.
        assertEquals(creds.get("username").asText(), "alice");
        assertEquals(creds.get("password").asText(), "s3cr=t$1"); // regex-special chars survive
    }

    /**
     * Scenario: a required environment variable is not set.
     * Assertion: FrameworkException whose message names TEST_USERNAME.
     */
    public void missingEnvVarFailsWithVariableName() {
        // Lookup returns null for every variable, simulating an unset environment.
        FrameworkException e = expectThrows(FrameworkException.class,
                () -> new TestDataLoader("qa").node("credentials", k -> null));
        // The message must say which variable to set.
        assertEquals(e.getMessage().contains("TEST_USERNAME"), true);
    }

    /**
     * Scenario: a required environment variable is set but empty.
     * Assertion: treated as missing, so FrameworkException is thrown.
     */
    public void emptyEnvVarIsTreatedAsMissing() {
        // Empty string must not be accepted as a credential.
        assertThrows(FrameworkException.class, () -> new TestDataLoader("qa").node("credentials", k -> ""));
    }

    /**
     * Scenario: requesting a node that does not exist, and loading an env with no data file.
     * Assertion: FrameworkException in both cases.
     */
    public void unknownKeyAndUnknownEnvAreRejected() {
        // Unknown top-level key.
        assertThrows(FrameworkException.class, () -> new TestDataLoader("qa").node("nope"));
        // Unknown environment name (no matching JSON file).
        assertThrows(FrameworkException.class, () -> new TestDataLoader("nonexistent-env"));
    }

    /**
     * Scenario: a node without placeholders is read while the environment lookup returns nothing.
     * Assertion: it loads fine (5 entries), so only nodes that use env vars require them.
     */
    public void nodesWithoutPlaceholdersNeedNoEnvironment() {
        // Lookup always returns null; it must not matter for this node.
        assertEquals(new TestDataLoader("qa").node("invalidLocators", k -> null).size(), 5);
    }
}
