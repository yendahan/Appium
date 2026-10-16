package data;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import config.ConfigManager;
import exceptions.FrameworkException;

import java.io.IOException;
import java.io.InputStream;
import java.util.Map;
import java.util.function.Function;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * Loads external test data from {@code testdata/<env>.json}.
 * String values of the form {@code ${env:NAME}} are replaced by the environment variable NAME when a node is
 * requested, so credentials are never stored in the repository.
 */
public final class TestDataLoader {

    private static final ObjectMapper MAPPER = new ObjectMapper();
    private static final Pattern PLACEHOLDER = Pattern.compile("\\$\\{env:([A-Za-z0-9_]+)}");

    private final JsonNode root;

    /**
     * Loads the data file for an environment.
     *
     * @param env environment name, e.g. "qa"
     * @throws FrameworkException if the file is missing or not valid JSON
     */
    public TestDataLoader(String env) {
        // Parse the whole file once; placeholders stay unresolved until a node is requested.
        this.root = read("testdata/" + env + ".json");
    }

    /**
     * Creates a loader for the environment selected by {@code -Denv}.
     *
     * @return a loader for the current environment
     */
    public static TestDataLoader forCurrentEnv() {
        // Reuse the configured env name so data and config profiles always match.
        return new TestDataLoader(ConfigManager.get().env());
    }

    /**
     * Returns the node at a top-level key with placeholders resolved from the process environment.
     *
     * @param key top-level key in the JSON file
     * @return a copy of the node with {@code ${env:NAME}} values substituted
     * @throws FrameworkException if the key is missing or a referenced variable is unset
     */
    public JsonNode node(String key) {
        // Use the real process environment as the placeholder source.
        return node(key, System::getenv);
    }

    /**
     * Same as {@link #node(String)} but with an injectable environment lookup (for tests).
     *
     * @param key       top-level key in the JSON file
     * @param envLookup function mapping a variable name to its value, or null if unset
     * @return a copy of the node with placeholders substituted
     * @throws FrameworkException if the key is missing or a referenced variable is unset
     */
    public JsonNode node(String key, Function<String, String> envLookup) {
        // Find the requested section of the data file.
        JsonNode found = root.get(key);
        // Fail with the key name so typos in tests are easy to find.
        if (found == null) {
            throw new FrameworkException("Test data key '" + key + "' not found");
        }
        // Resolve on a deep copy so secrets never get written back into the cached tree.
        return resolve(found.deepCopy(), envLookup);
    }

    /**
     * Recursively substitutes placeholders in all string values of a node.
     * Side effect: mutates object and array nodes in place (callers pass a copy).
     *
     * @param node      the node to resolve
     * @param envLookup function mapping a variable name to its value
     * @return the resolved node (a new text node for strings, otherwise the same mutated node)
     */
    private static JsonNode resolve(JsonNode node, Function<String, String> envLookup) {
        // Text nodes are immutable, so return a replacement node with placeholders substituted.
        if (node.isTextual()) {
            return MAPPER.getNodeFactory().textNode(substitute(node.asText(), envLookup));
        }
        // Objects: resolve each field value in place.
        if (node.isObject()) {
            // Cast is safe because isObject() was checked; ObjectNode allows in-place updates.
            ObjectNode obj = (ObjectNode) node;
            // Walk every field so nested placeholders are also replaced.
            for (Map.Entry<String, JsonNode> entry : obj.properties()) {
                // Replace the field value with its resolved version.
                entry.setValue(resolve(entry.getValue(), envLookup));
            }
        } else if (node.isArray()) {
            // Arrays: resolve each element in place.
            ArrayNode arr = (ArrayNode) node;
            // Index loop because elements are replaced while iterating.
            for (int i = 0; i < arr.size(); i++) {
                // Swap in the resolved element.
                arr.set(i, resolve(arr.get(i), envLookup));
            }
        }
        // Numbers, booleans and the mutated containers are returned as is.
        return node;
    }

    /**
     * Replaces every {@code ${env:NAME}} occurrence in a string.
     *
     * @param text      text possibly containing placeholders
     * @param envLookup function mapping a variable name to its value
     * @return the text with all placeholders replaced
     * @throws FrameworkException if a referenced variable is unset or empty
     */
    static String substitute(String text, Function<String, String> envLookup) {
        // Find each placeholder in the text.
        Matcher m = PLACEHOLDER.matcher(text);
        // Accumulate the output while copying the unmatched parts.
        StringBuilder out = new StringBuilder();
        // Process placeholders one by one, left to right.
        while (m.find()) {
            // Look up the variable named inside the placeholder.
            String value = envLookup.apply(m.group(1));
            // Missing credentials should stop the run now rather than send blanks to the app.
            if (value == null || value.isEmpty()) {
                // Name only the variable, never a value.
                throw new FrameworkException("Environment variable '" + m.group(1) + "' required by test data is not set");
            }
            // quoteReplacement stops '$' or '\' in the value from being read as regex syntax.
            m.appendReplacement(out, Matcher.quoteReplacement(value));
        }
        // Copy whatever follows the last placeholder.
        m.appendTail(out);
        // Return the fully substituted string.
        return out.toString();
    }

    /**
     * Reads and parses a JSON resource from the classpath.
     *
     * @param resource classpath-relative path of the file
     * @return the parsed JSON tree
     * @throws FrameworkException if the resource is missing or unparsable
     */
    private static JsonNode read(String resource) {
        // Try-with-resources closes the stream; the context loader finds files in src/test/resources.
        try (InputStream in = Thread.currentThread().getContextClassLoader().getResourceAsStream(resource)) {
            // A null stream means the file is not on the classpath (e.g. unknown -Denv).
            if (in == null) {
                throw new FrameworkException("Test data file '" + resource + "' not found on classpath");
            }
            // Parse the JSON into a tree for flexible lookup.
            return MAPPER.readTree(in);
        } catch (IOException e) {
            // Wrap I/O and parse errors with the file name for context.
            throw new FrameworkException("Unable to parse test data file '" + resource + "'", e);
        }
    }
}
