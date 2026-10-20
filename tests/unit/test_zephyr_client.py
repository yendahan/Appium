import pytest

from framework.zephyr_client import ZephyrClient

pytestmark = pytest.mark.unit


class FakeClient(ZephyrClient):
    """Records requests instead of calling Jira."""

    def __init__(self, folders, cases):
        super().__init__("https://example.test/v2", "token", "AMW")
        self.folders, self.cases, self.sent = folders, cases, []

    def _send(self, method, path, body=None):
        self.sent.append((method, path, body))
        if method == "POST" and path == "/folders":
            return {"id": 42}
        if path.startswith("/folders"):
            return {"values": self.folders}
        if method == "GET" and path.startswith("/testcases"):
            return {"values": self.cases}
        if method == "POST" and path == "/testcases":
            return {"key": "AMW-T9000"}
        return {}


FOLDERS = [{"id": 7, "name": "Mobile Automation"}]
STEPS = [("Open the app", "Welcome shows"), ("Tap SIGN UP!", "Verification Code shows")]


def test_create_case_posts_case_then_steps():
    client = FakeClient(FOLDERS, [])
    assert client.create_case("Case A", "Mobile Automation", "Objective", STEPS) == ("AMW-T9000", True)
    case_body = next(b for m, p, b in client.sent if m == "POST" and p == "/testcases")
    assert case_body == {"projectKey": "AMW", "name": "Case A", "folderId": 7, "objective": "Objective"}
    steps_body = next(b for m, p, b in client.sent if p == "/testcases/AMW-T9000/teststeps")
    assert steps_body["mode"] == "OVERWRITE"
    assert steps_body["items"][1] == {"inline": {"description": "Tap SIGN UP!",
                                                  "expectedResult": "Verification Code shows"}}


def test_create_case_reuses_existing_case_with_the_same_name():
    client = FakeClient(FOLDERS, [{"key": "AMW-T1", "name": "Case A"}])
    assert client.create_case("Case A", "Mobile Automation", "Objective", STEPS) == ("AMW-T1", False)
    assert not any(m == "POST" for m, _, _ in client.sent)


def test_create_case_fails_when_the_folder_is_missing():
    client = FakeClient([], [])
    with pytest.raises(IOError, match="Mobile Automation"):
        client.create_case("Case A", "Mobile Automation", "Objective", STEPS)
    assert not any(m == "POST" for m, _, _ in client.sent)


def test_case_keys_in_folder_lists_keys():
    client = FakeClient(FOLDERS, [{"key": "AMW-T1", "name": "A"}, {"key": "AMW-T2", "name": "B"}])
    assert client.case_keys_in_folder("Mobile Automation") == ["AMW-T1", "AMW-T2"]


def test_case_keys_in_folder_is_empty_list_for_an_empty_folder():
    assert FakeClient(FOLDERS, []).case_keys_in_folder("Mobile Automation") == []


def test_case_keys_in_folder_is_none_when_the_folder_does_not_exist():
    assert FakeClient(FOLDERS, []).case_keys_in_folder("No such folder") is None


def test_cases_in_folder_maps_names_to_keys():
    client = FakeClient(FOLDERS, [{"key": "AMW-T1", "name": "A"}, {"key": "AMW-T2", "name": "B"}])
    assert client.cases_in_folder("Mobile Automation") == {"A": "AMW-T1", "B": "AMW-T2"}


def test_cases_in_folder_distinguishes_empty_from_missing():
    assert FakeClient(FOLDERS, []).cases_in_folder("Mobile Automation") == {}
    assert FakeClient(FOLDERS, []).cases_in_folder("No such folder") is None


def test_create_folder_posts_a_top_level_test_case_folder():
    client = FakeClient([], [])
    assert client.create_folder("Sprint 42 regression") == 42
    assert client.sent[-1] == ("POST", "/folders", {"projectKey": "AMW", "name": "Sprint 42 regression",
                                                    "folderType": "TEST_CASE"})


def test_a_folder_the_client_just_created_is_used_even_if_zephyr_does_not_list_it_yet():
    client = FakeClient(FOLDERS, [])  # GET /folders still shows only the old folder
    folder_id = client.create_folder("Brand new")
    assert client.cases_in_folder("Brand new") == {}
    assert client.create_case("Case A", "Brand new", "Objective", STEPS) == ("AMW-T9000", True)
    case_body = next(b for m, p, b in client.sent if m == "POST" and p == "/testcases")
    assert case_body["folderId"] == folder_id


class TreeClient(ZephyrClient):
    """A Zephyr whose folder tree is kept in memory; ``lag`` hides folders created through the API from listings."""

    def __init__(self, folders, lag=False):
        super().__init__("https://example.test/v2", "token", "AMW")
        self.tree, self.lag, self.posts, self._next = [dict(f) for f in folders], lag, [], 100

    def _send(self, method, path, body=None):
        if method == "POST" and path == "/folders":
            self.posts.append(body)
            self._next += 1
            self.tree.append({"id": self._next, "name": body["name"], "parentId": body.get("parentId"), "new": True})
            return {"id": self._next}
        if path.startswith("/folders"):
            return {"values": [f for f in self.tree if not (self.lag and f.get("new"))]}
        if path.startswith("/testcases"):
            return {"values": []}
        return {}


TREE = [{"id": 1, "name": "Android", "parentId": None},
        {"id": 2, "name": "Upgraded Consumer Account", "parentId": 1},
        {"id": 3, "name": "Upgraded Consumer Account", "parentId": 9},  # same name under another parent
        {"id": 9, "name": "ios", "parentId": None}]


def test_a_nested_path_is_resolved_by_parent_not_by_name_alone():
    client = TreeClient(TREE)
    assert client._folder_id("Android/Upgraded Consumer Account") == 2
    assert client._folder_id("ios/Upgraded Consumer Account") == 3
    assert client._folder_id("Upgraded Consumer Account") is None  # not a top-level folder
    assert client._folder_id("Android") == 1


def test_a_missing_path_creates_each_level_with_the_right_parent():
    client = TreeClient([])
    leaf = client.create_folder("Android/Upgraded Consumer Account")
    assert [(p["name"], p.get("parentId")) for p in client.posts] == [
        ("Android", None), ("Upgraded Consumer Account", 101)]
    assert leaf == 102


def test_only_the_missing_levels_are_created():
    client = TreeClient([{"id": 1, "name": "Android", "parentId": None}])
    leaf = client.create_folder("Android/Upgraded Consumer Account")
    assert [p["name"] for p in client.posts] == ["Upgraded Consumer Account"]
    assert client.posts[0]["parentId"] == 1 and leaf == 101


def test_nothing_is_created_when_the_whole_path_exists():
    client = TreeClient(TREE)
    assert client.create_folder("Android/Upgraded Consumer Account") == 2
    assert client.posts == []


def test_a_just_created_nested_folder_is_found_even_if_zephyr_does_not_list_it_yet():
    client = TreeClient([], lag=True)
    leaf = client.create_folder("Android/Upgraded Consumer Account")
    assert client._folder_id("Android/Upgraded Consumer Account") == leaf
    assert client.cases_in_folder("Android/Upgraded Consumer Account") == {}


def test_spaces_around_the_separator_and_empty_parts_are_ignored():
    client = TreeClient(TREE)
    assert client._folder_id(" Android / Upgraded Consumer Account ") == 2
    assert client._folder_id("Android//Upgraded Consumer Account/") == 2


def test_an_empty_path_is_refused():
    with pytest.raises(ValueError):
        TreeClient([]).create_folder("  /  ")


class CaseClient(ZephyrClient):
    """Records requests; GET /testcases/<key> returns a loose case, the list returns two pages."""

    def __init__(self, pages, folders=None):
        super().__init__("https://example.test/v2", "token", "AMW")
        self.pages, self.folders, self.sent = pages, folders or [{"id": 7, "name": "Mobile Automation"}], []

    def _send(self, method, path, body=None):
        self.sent.append((method, path, body))
        if path.startswith("/folders"):
            return {"values": self.folders}
        if method == "GET" and path.startswith("/testcases?"):
            start = int(path.rsplit("startAt=", 1)[1])
            page = self.pages[0 if start == 0 else 1]
            return {"values": page, "isLast": start != 0}
        if method == "GET" and path.startswith("/testcases/"):
            return {"id": 11, "key": "AMW-T5", "name": "Case A", "project": {"id": 3}, "objective": "Objective",
                    "precondition": None, "estimatedTime": None, "labels": ["x"], "component": None,
                    "priority": {"id": 4}, "status": {"id": 5}, "folder": None, "owner": None,
                    "customFields": {}, "testScript": {"self": "..."}, "links": {"self": "..."}}
        return {}


def test_reusable_cases_reads_every_page_loose_first_then_cases_in_folders():
    page1 = [{"key": "YEN-T20", "name": "A", "folder": None}, {"key": "YEN-T3", "name": "A", "folder": None},
             {"key": "YEN-T4", "name": "B", "folder": {"id": 7}}, {"key": "YEN-T2", "name": "A", "folder": {"id": 7}}]
    page2 = [{"key": "YEN-T10", "name": "A", "folder": None}, {"key": "YEN-T1", "name": "A", "folder": {"id": 8}}]
    found = CaseClient([page1, page2]).reusable_cases()
    assert found["A"] == ["YEN-T3", "YEN-T10", "YEN-T20", "YEN-T1", "YEN-T2"]  # loose by key, then filed by key
    assert found["B"] == ["YEN-T4"]


def test_move_case_writes_the_case_back_with_only_the_folder_changed():
    client = CaseClient([[]])
    client.move_case("AMW-T5", "Mobile Automation")
    method, path, body = client.sent[-1]
    assert (method, path) == ("PUT", "/testcases/AMW-T5")
    assert body["folder"] == {"id": 7} and body["name"] == "Case A" and body["objective"] == "Objective"
    assert body["project"] == {"id": 3} and body["priority"] == {"id": 4} and body["status"] == {"id": 5}
    assert body["labels"] == ["x"] and "testScript" not in body and "links" not in body


def test_move_case_refuses_a_folder_that_does_not_exist():
    client = CaseClient([[]])
    with pytest.raises(IOError, match="not found"):
        client.move_case("AMW-T5", "No such folder")
    assert not any(m == "PUT" for m, _, _ in client.sent)


def test_unfile_case_writes_the_case_back_with_no_folder():
    client = CaseClient([[]])
    client.unfile_case("AMW-T5")
    method, path, body = client.sent[-1]
    assert (method, path) == ("PUT", "/testcases/AMW-T5")
    assert body["folder"] is None and body["name"] == "Case A" and body["project"] == {"id": 3}


def test_list_cases_keeps_duplicate_names_and_cases_in_folder_collapses_them():
    class Listing(FakeClient):
        pass
    client = Listing(FOLDERS, [{"key": "AMW-T1", "name": "A"}, {"key": "AMW-T2", "name": "A"}])
    assert client.list_cases("Mobile Automation") == [("A", "AMW-T1"), ("A", "AMW-T2")]
    assert client.list_cases("No such folder") is None
    assert client.cases_in_folder("Mobile Automation") == {"A": "AMW-T2"}
