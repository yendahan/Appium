package integrations;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;

import java.io.IOException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;
import java.util.LinkedHashMap;
import java.util.Map;

/** Minimal Zephyr Scale Cloud (v2) client: creates a test cycle and posts test executions. Token is supplied by the caller, never stored. */
public class ZephyrClient {

    private static final ObjectMapper JSON = new ObjectMapper();

    private final HttpClient http = HttpClient.newBuilder().connectTimeout(Duration.ofSeconds(10)).build();
    private final String baseUrl;
    private final String token;
    private final String projectKey;

    /**
     * @param baseUrl    API root, e.g. https://api.zephyrscale.smartbear.com/v2
     * @param token      Zephyr API access token
     * @param projectKey Jira project key that has Zephyr enabled
     */
    public ZephyrClient(String baseUrl, String token, String projectKey) {
        this.baseUrl = baseUrl.endsWith("/") ? baseUrl.substring(0, baseUrl.length() - 1) : baseUrl;
        this.token = token;
        this.projectKey = projectKey;
    }

    /**
     * Creates a test cycle.
     *
     * @param name cycle name
     * @return the new cycle key (e.g. BAY-R12)
     * @throws IOException on HTTP or network failure
     */
    public String createCycle(String name) throws IOException {
        JsonNode res = post("/testcycles", Map.of("projectKey", projectKey, "name", name));
        return res.path("key").asText();
    }

    /**
     * Records one execution result.
     *
     * @param cycleKey   cycle to add to
     * @param caseKey    Zephyr test case key
     * @param statusName Zephyr status name, e.g. Pass, Fail, Not Executed
     * @param comment    optional comment (may be null)
     * @throws IOException on HTTP or network failure
     */
    public String postExecution(String cycleKey, String caseKey, String statusName, String comment) throws IOException {
        Map<String, Object> body = new LinkedHashMap<>();
        body.put("projectKey", projectKey);
        body.put("testCaseKey", caseKey);
        body.put("testCycleKey", cycleKey);
        body.put("statusName", statusName);
        if (comment != null) {
            body.put("comment", comment);
        }
        JsonNode res = post("/testexecutions", body);
        // Cloud returns the numeric id (and self link); the key is not always present.
        return res.hasNonNull("key") ? res.path("key").asText() : res.path("id").asText();
    }

    /**
     * Sets every step of an execution to one status, with an actual result (the steps are copied from the test case).
     * The framework cannot tell which step failed, so all steps share the overall result.
     *
     * @param executionKey execution key returned by {@link #postExecution}
     * @param statusName   Zephyr step status name, e.g. Pass or Fail
     * @param actual       actual result text for each step
     * @param lastStepNote optional extra line appended to the last step's actual result (e.g. a screenshot path); may be null
     * @throws IOException on HTTP or network failure
     */
    public void updateStepResults(String executionKey, String statusName, String actual, String lastStepNote) throws IOException {
        JsonNode steps = get("/testexecutions/" + executionKey + "/teststeps").path("values");
        java.util.List<Map<String, Object>> items = new java.util.ArrayList<>();
        for (int i = 0; i < steps.size(); i++) {
            Map<String, Object> item = new LinkedHashMap<>();
            item.put("statusName", statusName);
            boolean last = i == steps.size() - 1;
            item.put("actualResult", last && lastStepNote != null ? actual + "\n" + lastStepNote : actual);
            items.add(item);
        }
        if (!items.isEmpty()) {
            send("PUT", "/testexecutions/" + executionKey + "/teststeps", Map.of("steps", items));
        }
    }

    /**
     * Lists the keys of all test cases in a folder (by folder name) of the project.
     *
     * @param folderName test case folder name, e.g. Mobile Automation
     * @return case keys; empty if the folder does not exist
     * @throws IOException on HTTP or network failure
     */
    public java.util.List<String> caseKeysInFolder(String folderName) throws IOException {
        java.util.List<String> keys = new java.util.ArrayList<>();
        long folderId = -1;
        for (JsonNode f : get("/folders?projectKey=" + projectKey + "&folderType=TEST_CASE&maxResults=500").path("values")) {
            if (folderName.equals(f.path("name").asText())) {
                folderId = f.path("id").asLong();
            }
        }
        if (folderId < 0) {
            return keys;
        }
        for (JsonNode c : get("/testcases?projectKey=" + projectKey + "&folderId=" + folderId + "&maxResults=500").path("values")) {
            keys.add(c.path("key").asText());
        }
        return keys;
    }

    /**
     * Maps each test case key to its latest execution key in a cycle.
     *
     * @param cycleKey cycle to read
     * @return case key to execution key (the one with the highest id wins)
     * @throws IOException on HTTP or network failure
     */
    public Map<String, String> latestExecutions(String cycleKey) throws IOException {
        Map<String, String> byCase = new LinkedHashMap<>();
        Map<String, Long> ids = new LinkedHashMap<>();
        for (JsonNode e : get("/testexecutions?projectKey=" + projectKey + "&testCycle=" + cycleKey + "&maxResults=500").path("values")) {
            String[] parts = e.path("testCase").path("self").asText().split("/");
            String caseKey = parts.length >= 3 ? parts[parts.length - 3] : "";
            long id = e.path("id").asLong();
            if (!caseKey.isEmpty() && id > ids.getOrDefault(caseKey, -1L)) {
                ids.put(caseKey, id);
                byCase.put(caseKey, e.path("key").asText());
            }
        }
        return byCase;
    }

    /**
     * Updates an existing execution's status and comment.
     *
     * @param executionKey execution to update
     * @param statusName   Zephyr status name, e.g. Pass, Fail, Not Executed
     * @param comment      optional comment (may be null)
     * @throws IOException on HTTP or network failure
     */
    public void updateExecution(String executionKey, String statusName, String comment) throws IOException {
        Map<String, Object> body = new LinkedHashMap<>();
        body.put("statusName", statusName);
        if (comment != null) {
            body.put("comment", comment);
        }
        send("PUT", "/testexecutions/" + executionKey, body);
    }

    private JsonNode get(String path) throws IOException {
        return send("GET", path, null);
    }

    private JsonNode post(String path, Object body) throws IOException {
        return send("POST", path, body);
    }

    private JsonNode send(String method, String path, Object body) throws IOException {
        HttpRequest.BodyPublisher pub = body == null ? HttpRequest.BodyPublishers.noBody()
                : HttpRequest.BodyPublishers.ofString(JSON.writeValueAsString(body));
        HttpRequest req = HttpRequest.newBuilder(URI.create(baseUrl + path))
                .timeout(Duration.ofSeconds(20))
                .header("Authorization", "Bearer " + token)
                .header("Content-Type", "application/json")
                .method(method, pub)
                .build();
        try {
            HttpResponse<String> res = http.send(req, HttpResponse.BodyHandlers.ofString());
            if (res.statusCode() / 100 != 2) {
                throw new IOException("Zephyr " + path + " returned " + res.statusCode() + ": " + res.body());
            }
            return res.body() == null || res.body().isBlank() ? JSON.createObjectNode() : JSON.readTree(res.body());
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            throw new IOException("Interrupted calling Zephyr " + path, e);
        }
    }
}
