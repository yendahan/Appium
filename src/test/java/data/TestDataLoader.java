package data;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import config.ConfigManager;
import exceptions.FrameworkException;

import java.io.IOException;
import java.io.InputStream;
import java.util.Iterator;
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

    public TestDataLoader(String env) {
        this.root = read("testdata/" + env + ".json");
    }

    public static TestDataLoader forCurrentEnv() {
        return new TestDataLoader(ConfigManager.get().env());
    }

    /** Returns the node at a top-level key with placeholders resolved from the process environment. */
    public JsonNode node(String key) {
        return node(key, System::getenv);
    }

    public JsonNode node(String key, Function<String, String> envLookup) {
        JsonNode found = root.get(key);
        if (found == null) {
            throw new FrameworkException("Test data key '" + key + "' not found");
        }
        return resolve(found.deepCopy(), envLookup);
    }

    private static JsonNode resolve(JsonNode node, Function<String, String> envLookup) {
        if (node.isTextual()) {
            return MAPPER.getNodeFactory().textNode(substitute(node.asText(), envLookup));
        }
        if (node.isObject()) {
            ObjectNode obj = (ObjectNode) node;
            for (Iterator<Map.Entry<String, JsonNode>> it = obj.fields(); it.hasNext(); ) {
                Map.Entry<String, JsonNode> entry = it.next();
                entry.setValue(resolve(entry.getValue(), envLookup));
            }
        } else if (node.isArray()) {
            ArrayNode arr = (ArrayNode) node;
            for (int i = 0; i < arr.size(); i++) {
                arr.set(i, resolve(arr.get(i), envLookup));
            }
        }
        return node;
    }

    static String substitute(String text, Function<String, String> envLookup) {
        Matcher m = PLACEHOLDER.matcher(text);
        StringBuilder out = new StringBuilder();
        while (m.find()) {
            String value = envLookup.apply(m.group(1));
            if (value == null || value.isEmpty()) {
                throw new FrameworkException("Environment variable '" + m.group(1) + "' required by test data is not set");
            }
            m.appendReplacement(out, Matcher.quoteReplacement(value));
        }
        m.appendTail(out);
        return out.toString();
    }

    private static JsonNode read(String resource) {
        try (InputStream in = Thread.currentThread().getContextClassLoader().getResourceAsStream(resource)) {
            if (in == null) {
                throw new FrameworkException("Test data file '" + resource + "' not found on classpath");
            }
            return MAPPER.readTree(in);
        } catch (IOException e) {
            throw new FrameworkException("Unable to parse test data file '" + resource + "'", e);
        }
    }
}
