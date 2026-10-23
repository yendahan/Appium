from collections import Counter
from datetime import datetime

import pytest

from framework import zephyr_cases, zephyr_reporter
from framework.config_manager import ConfigManager

pytestmark = pytest.mark.unit

NOW = datetime(2026, 10, 19, 17, 30)
STAMP = "2026-10-19 17:30"
SUB = "Android/Upgraded Consumer Account"  # where the test files sit under tests/
LOGIN_TEST = "tests/Android/Upgraded Consumer Account/test_login.py::test_wrong_password_is_rejected"
LOGIN_CASE = zephyr_cases.CASES["test_login.py::test_wrong_password_is_rejected"].name
# These tests exercise one project folder; the Asenso copies of the cases are covered in test_zephyr_cases.py.
UPGRADED = {k: c for k, c in zephyr_cases.CASES.items() if "test_asenso_" not in k and "test_basic_account_" not in k}
ALL_CASES = {c.name: f"AMW-T{i}" for i, c in enumerate(UPGRADED.values(), start=1)}


class FakeClient:
    """Stands in for ZephyrClient. `folders` maps a folder path to {case name: key}; a missing path means the
    folder does not exist.

    `fail` names a call that raises; `lag` makes cases_in_folder return stale (empty) data after the first call,
    like a Zephyr listing that has not caught up with what was just created.
    """

    def __init__(self, folders=None, fail=None, lag=False, loose=None, dupes=None):
        self.folders = {path: dict(cases) for path, cases in (folders or {}).items()}
        self.dupes = {path: list(extra) for path, extra in (dupes or {}).items()}  # more cases, same names, in a folder
        self.unfiled = []
        self.fail, self.lag, self.reads = fail, lag, 0
        self.loose = {name: list(keys) for name, keys in (loose or {}).items()}  # existing cases in no folder
        self.loose_scans, self.moved = 0, []
        self.created_folders, self.created_cases, self.created, self.posted = [], [], [], []

    def _maybe_fail(self, call):
        if self.fail == call:
            raise IOError(f"{call} returned 403: forbidden")

    def cases_in_folder(self, path):
        self._maybe_fail("cases_in_folder")
        self.reads += 1
        if self.lag and self.reads > 1:
            return {}
        return dict(self.folders[path]) if path in self.folders else None

    def create_folder(self, path):
        self._maybe_fail("create_folder")
        self.created_folders.append(path)
        self.folders[path] = {}
        return 1

    def create_case(self, name, path, objective, steps):
        self._maybe_fail("create_case")
        self.created_cases.append((path, name))
        self.folders[path][name] = f"AMW-T{9000 + len(self.created_cases)}"
        return self.folders[path][name], True

    def list_cases(self, path):
        self._maybe_fail("list_cases")
        if path not in self.folders:
            return None
        return list(self.folders[path].items()) + list(self.dupes.get(path, []))

    def reusable_cases(self):
        self._maybe_fail("reusable_cases")
        self.loose_scans += 1
        return {name: list(keys) for name, keys in self.loose.items()}

    def move_case(self, key, path):
        self._maybe_fail("move_case")
        for folder, cases in list(self.folders.items()):  # a case is in one place: take it out of where it was
            for name, k in list(cases.items()):
                if k == key:
                    del cases[name]
                    self.moved_name = name
        name = next((n for n, keys in self.loose.items() if key in keys), None) or getattr(self, "moved_name", "?")
        self.moved.append((key, path))
        self.folders[path][name] = key

    def unfile_case(self, key):
        self._maybe_fail("unfile_case")
        self.unfiled.append(key)
        for path, cases in self.folders.items():
            for name, k in list(cases.items()):
                if k == key:
                    del cases[name]
        for path, extra in self.dupes.items():
            self.dupes[path] = [(n, k) for n, k in extra if k != key]

    def create_cycle(self, name):
        self._maybe_fail("create_cycle")
        self.created.append(name)
        return "AMW-R900"

    def latest_executions(self, cycle_key):
        return {}

    def post_execution(self, cycle_key, case_key, status, comment):
        self.posted.append((cycle_key, case_key, status))
        return f"EXEC-{case_key}"

    def update_execution(self, execution_key, status, comment):
        pass


@pytest.fixture
def setup(monkeypatch):
    """Clean reporter state, a token, and no Zephyr settings from the environment; returns a config builder."""
    for var in ("ZEPHYR_CYCLE_NAME", "ZEPHYR_CASES_FOLDER", "ZEPHYR_CYCLE_KEY"):
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setenv("ZEPHYR_TOKEN", "token")
    monkeypatch.setattr(zephyr_cases, "CASES", UPGRADED)
    monkeypatch.setattr(zephyr_reporter, "_initialised", False)
    monkeypatch.setattr(zephyr_reporter, "_client", None)
    monkeypatch.setattr(zephyr_reporter, "_cycle_key", None)
    monkeypatch.setattr(zephyr_reporter, "_executions", {})
    monkeypatch.setattr(zephyr_reporter, "_case_keys_by_name", {})
    monkeypatch.setattr(zephyr_reporter, "_info", {})
    monkeypatch.setattr(zephyr_reporter, "_results", Counter())
    monkeypatch.setattr(zephyr_reporter, "_unpublished", [])

    def configure(name=None, folder=None, key=None):
        overrides = {k: v for k, v in (("zephyr.cycle.name", name), ("zephyr.cases.folder", folder),
                                       ("zephyr.cycle.key", key)) if v}
        monkeypatch.setattr(ConfigManager, "_instance", ConfigManager("qa", "emulator", overrides))

    return configure


def test_cycle_name_is_always_the_name_plus_date_and_time(setup):
    setup(name="Smoke test")
    assert zephyr_reporter.cycle_name(ConfigManager.get_instance(), STAMP) == f"Smoke test {STAMP}"


def test_the_folder_you_set_is_the_top_and_the_project_folders_are_created_below_it(setup):
    setup(name="Smoke test", folder="Regression")
    client = FakeClient()  # nothing exists, e.g. you deleted the folders
    zephyr_reporter.start_run(client, NOW)
    assert client.created_folders == [f"Regression/{SUB}"]  # the client creates every missing level of the path
    assert {path for path, _ in client.created_cases} == {f"Regression/{SUB}"}
    assert sorted(name for _, name in client.created_cases) == sorted(ALL_CASES)
    assert client.created == [f"Smoke test {STAMP}"]
    assert len(client.posted) == len(ALL_CASES)


def test_a_folder_path_you_set_is_kept_as_the_top(setup):
    setup(name="Smoke test", folder="Sprint 42/Regression")
    client = FakeClient()
    zephyr_reporter.start_run(client, NOW)
    assert client.created_folders == [f"Sprint 42/Regression/{SUB}"]


def test_a_complete_tree_creates_nothing_but_the_cycle(setup):
    setup(name="Smoke test", folder="Regression")
    client = FakeClient({f"Regression/{SUB}": ALL_CASES})
    zephyr_reporter.start_run(client, NOW)
    assert client.created_folders == [] and client.created_cases == []
    assert client.created == [f"Smoke test {STAMP}"]
    assert len(client.posted) == len(ALL_CASES)


def test_an_existing_empty_leaf_is_filled_on_a_rerun(setup):
    setup(name="Smoke test", folder="Regression")
    client = FakeClient({f"Regression/{SUB}": {}})  # left behind by an earlier failed run
    zephyr_reporter.start_run(client, NOW)
    assert client.created_folders == [] and len(client.created_cases) == len(ALL_CASES)


def test_a_leaf_with_only_some_cases_gets_just_the_missing_ones(setup):
    setup(name="Smoke test", folder="Regression")
    client = FakeClient({f"Regression/{SUB}": {LOGIN_CASE: "AMW-T77", "Hand-made case": "AMW-T78"}})
    zephyr_reporter.start_run(client, NOW)
    assert LOGIN_CASE not in [name for _, name in client.created_cases]
    assert len(client.created_cases) == len(ALL_CASES) - 1


def test_cases_left_directly_in_the_top_folder_by_the_old_layout_are_moved_down(setup):
    setup(name="Smoke test", folder="Regression")
    client = FakeClient({"Regression": ALL_CASES})  # the old layout: cases straight in the folder
    zephyr_reporter.start_run(client, NOW)
    assert client.created_folders == [f"Regression/{SUB}"]
    assert len(client.moved) == len(ALL_CASES) and client.created_cases == []
    assert client.folders["Regression"] == {}


LOOSE_ALL = {c.name: [f"AMW-T{500 + i}", f"AMW-T{900 + i}"] for i, c in enumerate(UPGRADED.values())}


def test_existing_loose_cases_are_moved_in_instead_of_creating_new_ones(setup):
    setup(name="Smoke test", folder="Regression")
    client = FakeClient(loose=LOOSE_ALL)
    zephyr_reporter.start_run(client, NOW)
    assert client.created_cases == []
    assert len(client.moved) == len(ALL_CASES) and {path for _, path in client.moved} == {f"Regression/{SUB}"}
    assert len(client.posted) == len(ALL_CASES)
    assert f"{len(ALL_CASES)} cases: {len(ALL_CASES)} moved in from existing, 0 created" in zephyr_reporter.summary()


def test_the_lowest_key_is_moved_first(setup):
    setup(name="Smoke test", folder="Regression")
    client = FakeClient(loose=LOOSE_ALL)
    zephyr_reporter.start_run(client, NOW)
    first = next(iter(UPGRADED.values())).name
    assert dict((key, path) for key, path in client.moved)["AMW-T500"].endswith(SUB)
    assert zephyr_reporter._case_keys_by_name[first] == "AMW-T500"


def test_a_name_with_no_loose_copy_is_created(setup):
    setup(name="Smoke test", folder="Regression")
    partial = {name: keys for name, keys in list(LOOSE_ALL.items())[:5]}
    client = FakeClient(loose=partial)
    zephyr_reporter.start_run(client, NOW)
    assert len(client.moved) == 5 and len(client.created_cases) == len(ALL_CASES) - 5


def test_a_case_that_sits_in_another_folder_is_moved_to_the_new_folder_instead_of_creating_a_copy(setup):
    setup(name="Smoke test", folder="Test102")
    old_tree = f"Test101/{SUB}"
    # the pool lists copies in no folder first and copies in other folders after them, as reusable_cases() does
    client = FakeClient({old_tree: ALL_CASES}, loose={name: [key] for name, key in ALL_CASES.items()})
    zephyr_reporter.start_run(client, NOW)
    assert client.created_cases == []
    assert {path for _, path in client.moved} == {f"Test102/{SUB}"}
    assert client.folders[old_tree] == {}  # the old folder lost them: no duplicates
    assert sum(len(v) for v in client.folders.values()) == len(ALL_CASES)  # the number of cases did not grow


def test_a_new_case_is_created_only_when_no_case_with_that_name_exists_anywhere(setup):
    setup(name="Smoke test", folder="Test102")
    first = next(iter(ALL_CASES))
    client = FakeClient({f"Test101/{SUB}": {first: ALL_CASES[first]}}, loose={first: [ALL_CASES[first]]})
    zephyr_reporter.start_run(client, NOW)
    assert len(client.moved) == 1 and len(client.created_cases) == len(ALL_CASES) - 1


def test_a_failing_move_falls_back_to_creating_the_case(setup):
    setup(name="Smoke test", folder="Regression")
    client = FakeClient(loose=LOOSE_ALL, fail="move_case")
    zephyr_reporter.start_run(client, NOW)  # no exception
    assert client.moved == [] and len(client.created_cases) == len(ALL_CASES)


def test_failing_to_look_for_reusable_cases_falls_back_to_creating(setup):
    setup(name="Smoke test", folder="Regression")
    client = FakeClient(loose=LOOSE_ALL, fail="reusable_cases")
    zephyr_reporter.start_run(client, NOW)
    assert len(client.created_cases) == len(ALL_CASES)


def test_nothing_is_scanned_or_moved_when_the_folder_already_has_every_case(setup):
    setup(name="Smoke test", folder="Regression")
    client = FakeClient({f"Regression/{SUB}": ALL_CASES}, loose=LOOSE_ALL)
    zephyr_reporter.start_run(client, NOW)
    assert client.loose_scans == 0 and client.moved == [] and client.created_cases == []


TOP_AND_ANDROID = ("Regression", "Regression/Android")


def test_a_defined_case_in_an_upper_folder_is_pulled_down_into_the_innermost_folder(setup):
    setup(name="Smoke test", folder="Regression")
    client = FakeClient({"Regression": {LOGIN_CASE: "AMW-T7"}, f"Regression/{SUB}": {}})
    zephyr_reporter.start_run(client, NOW)
    assert ("AMW-T7", f"Regression/{SUB}") in client.moved
    assert LOGIN_CASE not in client.folders["Regression"]
    assert LOGIN_CASE not in [name for _, name in client.created_cases]  # it was reused, not created again
    assert zephyr_reporter._case_keys_by_name[LOGIN_CASE] == "AMW-T7"
    assert "1 pulled down from upper folders" in zephyr_reporter.summary()


def test_a_duplicate_in_an_upper_folder_is_taken_out_when_the_innermost_has_it(setup):
    setup(name="Smoke test", folder="Regression")
    client = FakeClient({f"Regression/{SUB}": ALL_CASES, "Regression/Android": {}},
                        dupes={"Regression/Android": [(LOGIN_CASE, "AMW-T888")]})
    zephyr_reporter.start_run(client, NOW)
    assert client.unfiled == ["AMW-T888"] and client.moved == []
    assert "1 duplicates taken out of upper folders" in zephyr_reporter.summary()
    assert zephyr_reporter._case_keys_by_name[LOGIN_CASE] == ALL_CASES[LOGIN_CASE]  # the innermost copy is kept


def test_only_one_copy_is_pulled_down_and_the_rest_are_taken_out(setup):
    setup(name="Smoke test", folder="Regression")
    client = FakeClient({"Regression": {LOGIN_CASE: "AMW-T7"}, f"Regression/{SUB}": {}},
                        dupes={"Regression": [(LOGIN_CASE, "AMW-T8")]})
    zephyr_reporter.start_run(client, NOW)
    assert client.moved[0] == ("AMW-T7", f"Regression/{SUB}") and client.unfiled == ["AMW-T8"]


def test_other_cases_in_the_upper_folders_are_left_alone(setup):
    setup(name="Smoke test", folder="Regression")
    client = FakeClient({"Regression": {"My own case": "AMW-T50"}, f"Regression/{SUB}": ALL_CASES})
    zephyr_reporter.start_run(client, NOW)
    assert client.moved == [] and client.unfiled == []
    assert client.folders["Regression"] == {"My own case": "AMW-T50"}


def test_clean_upper_folders_change_nothing(setup):
    setup(name="Smoke test", folder="Regression")
    client = FakeClient({"Regression": {}, "Regression/Android": {}, f"Regression/{SUB}": ALL_CASES})
    zephyr_reporter.start_run(client, NOW)
    assert client.moved == [] and client.unfiled == [] and client.created_cases == []
    assert "pulled down" not in zephyr_reporter.summary()


def test_a_failure_tidying_an_upper_folder_does_not_stop_the_run(setup):
    setup(name="Smoke test", folder="Regression")
    client = FakeClient({"Regression": {LOGIN_CASE: "AMW-T7"}, f"Regression/{SUB}": ALL_CASES}, fail="unfile_case")
    zephyr_reporter.start_run(client, NOW)  # no exception: the leftover stays, with a warning
    assert client.created == [f"Smoke test {STAMP}"]


def test_missing_cycle_name_stops_the_run(setup):
    setup(folder="Regression")
    client = FakeClient()
    with pytest.raises(zephyr_reporter.ZephyrSetupError, match="ZEPHYR_CYCLE_NAME"):
        zephyr_reporter.start_run(client, NOW)
    assert client.created == [] and client.created_cases == []


def test_folder_not_set_stops_the_run(setup):
    setup(name="Smoke test")
    client = FakeClient()
    with pytest.raises(zephyr_reporter.ZephyrSetupError, match="ZEPHYR_CASES_FOLDER is not set"):
        zephyr_reporter.start_run(client, NOW)
    assert client.created == [] and client.created_folders == []


def test_a_cycle_key_is_ignored_and_a_new_cycle_is_created(setup):
    setup(name="Smoke test", folder="Regression", key="AMW-R5")
    client = FakeClient()
    zephyr_reporter.start_run(client, NOW)
    assert client.created == [f"Smoke test {STAMP}"]
    assert all(cycle == "AMW-R900" for cycle, _, _ in client.posted)


def test_a_listing_that_lags_behind_does_not_lose_the_created_cases(setup):
    setup(name="Smoke test", folder="Regression Testing")
    client = FakeClient(lag=True)  # re-listing after creation would come back empty
    zephyr_reporter.start_run(client, NOW)
    assert client.created_folders == [f"Regression Testing/{SUB}"]
    assert len(client.created_cases) == len(ALL_CASES)
    assert zephyr_reporter.resolve(LOGIN_TEST) is not None
    assert len(client.posted) == len(ALL_CASES)


def test_failing_to_create_a_case_stops_the_run_with_the_reason(setup):
    setup(name="Smoke test", folder="Regression Testing")
    client = FakeClient(fail="create_case")
    with pytest.raises(zephyr_reporter.ZephyrSetupError) as err:
        zephyr_reporter.start_run(client, NOW)
    message = str(err.value)
    assert "could not create test case" in message and "403" in message
    assert f"'Regression Testing/{SUB}' were created; run again to fill them" in message
    assert client.created == [] and zephyr_reporter._client is None


def test_failing_to_create_the_folder_stops_the_run_with_the_reason(setup):
    setup(name="Smoke test", folder="Regression Testing")
    client = FakeClient(fail="create_folder")
    with pytest.raises(zephyr_reporter.ZephyrSetupError, match="while creating folder 'Regression Testing/.*403"):
        zephyr_reporter.start_run(client, NOW)
    assert client.created == []


def test_failing_to_create_the_cycle_stops_the_run_with_the_reason(setup):
    setup(name="Smoke test", folder="Regression")
    with pytest.raises(zephyr_reporter.ZephyrSetupError, match="while creating the cycle.*403"):
        zephyr_reporter.start_run(FakeClient({f"Regression/{SUB}": ALL_CASES}, fail="create_cycle"), NOW)


def test_jira_being_down_at_setup_stops_the_run_and_says_how_to_skip_zephyr(setup):
    setup(name="Smoke test", folder="Regression")
    with pytest.raises(zephyr_reporter.ZephyrSetupError, match="while reading folder.*unset ZEPHYR_TOKEN"):
        zephyr_reporter.start_run(FakeClient(fail="cases_in_folder"), NOW)


def test_nothing_happens_without_a_token(setup, monkeypatch):
    setup()
    monkeypatch.delenv("ZEPHYR_TOKEN")
    zephyr_reporter.start_run(FakeClient(), NOW)  # no name or folder, but also no error
    assert zephyr_reporter._client is None


def test_a_test_reports_only_to_the_case_with_its_name_in_its_folder(setup):
    setup(name="Smoke test", folder="Regression")
    zephyr_reporter.start_run(FakeClient({f"Regression/{SUB}": {LOGIN_CASE: "AMW-T777"}}), NOW)
    assert zephyr_reporter.resolve(LOGIN_TEST) == "AMW-T777"


def test_a_parametrized_test_resolves_by_its_function(setup):
    setup(name="Smoke test", folder="Regression")
    client = FakeClient()
    zephyr_reporter.start_run(client, NOW)
    key = zephyr_reporter.resolve(
        "tests/Android/Upgraded Consumer Account/test_send_money.py::test_via_qr_valid[QRP2P - Static]")
    assert key == client.folders[f"Regression/{SUB}"][zephyr_cases.CASES["test_send_money.py::test_via_qr_valid"].name]


def test_a_test_with_no_defined_case_has_nowhere_to_report(setup):
    setup(name="Smoke test", folder="Regression")
    zephyr_reporter.start_run(FakeClient(), NOW)
    assert zephyr_reporter.resolve("tests/Android/Upgraded Consumer Account/test_unknown.py::test_x") is None


def test_summary_says_what_was_created_and_the_results(setup):
    setup(name="Smoke test", folder="Sprint 42 regression")
    zephyr_reporter.start_run(FakeClient(), NOW)
    zephyr_reporter._results.update(["Pass", "Pass", "Fail"])
    line = zephyr_reporter.summary()
    assert f"folder 'Sprint 42 regression/{SUB}' (created," in line
    assert f"{len(zephyr_cases.CASES)} cases: 0 moved in from existing, {len(zephyr_cases.CASES)} created" in line
    assert f"cycle AMW-R900 'Smoke test {STAMP}'" in line
    assert "results: 1 Fail, 2 Pass" in line


def test_a_failed_login_in_a_fixture_is_published_as_a_fail(setup):
    setup(name="Smoke test", folder="Regression")
    client = FakeClient()
    zephyr_reporter.start_run(client, NOW)
    key = zephyr_reporter.resolve(LOGIN_TEST)
    updates = []
    client.update_execution = lambda exec_key, status, comment: updates.append((exec_key, status, comment))
    zephyr_reporter.publish(key, "Fail", "AssertionError('Biometric setup is offered after first login')", None)
    assert updates == [(f"EXEC-{key}", "Fail", "Actual: AssertionError('Biometric setup is offered after first login')")]
    assert "results: 1 Fail" in zephyr_reporter.summary()


def test_a_result_that_cannot_be_published_is_named_in_the_summary(setup):
    setup(name="Smoke test", folder="Regression")
    client = FakeClient()
    zephyr_reporter.start_run(client, NOW)
    client.post_execution = lambda *a: (_ for _ in ()).throw(IOError("500"))
    zephyr_reporter.publish("AMW-T1", "Fail", "boom", None)
    assert "results: no results | not published: AMW-T1" in zephyr_reporter.summary()


def test_no_summary_when_zephyr_was_not_used(setup):
    setup()
    assert zephyr_reporter.summary() is None


# --- step results ---------------------------------------------------------------------------------------------
PAY_BILLS_EXPECTED = [c for c in zephyr_cases.CASES["test_pay_bills.py::test_pay_bills_manila_water"].steps]
PAY_BILLS_EXPECTED = [expected for _, expected in PAY_BILLS_EXPECTED]


def statuses(items):
    return [i["statusName"] for i in items]


def test_a_pass_gives_every_step_its_own_actual_result():
    items = zephyr_reporter.step_results(PAY_BILLS_EXPECTED, "Pass", None, None)
    assert statuses(items) == ["Pass"] * len(PAY_BILLS_EXPECTED)
    assert [i["actualResult"] for i in items][0] == "The Welcome screen is displayed"
    assert len({i["actualResult"] for i in items}) == len(items)  # no two steps share the same text


def test_the_screenshot_note_goes_on_the_last_step_of_a_pass():
    items = zephyr_reporter.step_results(PAY_BILLS_EXPECTED, "Pass", None, "Screenshot: a.png")
    assert items[-1]["actualResult"].endswith("<br>Screenshot: a.png")
    assert "Screenshot" not in items[0]["actualResult"]


def test_a_failure_is_put_on_its_own_step_with_the_steps_around_it_marked():
    error = "AssertionError('Biometric setup is offered after first login')"
    items = zephyr_reporter.step_results(PAY_BILLS_EXPECTED, "Fail", error, "Screenshot: a.png")
    assert statuses(items) == ["Pass", "Fail"] + ["Not Executed"] * (len(PAY_BILLS_EXPECTED) - 2)
    assert "Biometric setup is offered" in items[1]["actualResult"] and "Screenshot" in items[1]["actualResult"]
    assert items[0]["actualResult"] == "The Welcome screen is displayed"
    assert items[-1]["actualResult"] == "Not executed: an earlier step failed"


def test_a_receipt_failure_lands_on_the_last_step():
    error = "AssertionError(\"Receipt should show 'Payment Successful!' after CONFIRM\")"
    items = zephyr_reporter.step_results(PAY_BILLS_EXPECTED, "Fail", error, None)
    assert statuses(items) == ["Pass"] * (len(PAY_BILLS_EXPECTED) - 1) + ["Fail"]


def test_a_failure_that_cannot_be_placed_goes_on_the_last_step_only():
    items = zephyr_reporter.step_results(PAY_BILLS_EXPECTED, "Fail", "TimeoutException('weird')", None)
    assert statuses(items)[-1] == "Fail"
    assert statuses(items)[:-1] == ["Pass"] * (len(PAY_BILLS_EXPECTED) - 1)


def test_the_failure_text_is_escaped_for_html():
    items = zephyr_reporter.step_results(["The receipt shows 'Payment Successful!'"], "Fail", "a < b & c", None)
    assert items[0]["actualResult"] == "a &lt; b &amp; c"


def test_a_skipped_test_marks_every_step_blocked():
    items = zephyr_reporter.step_results(["one", "two"], "Blocked", None, None)
    assert statuses(items) == ["Blocked", "Blocked"] and items[0]["actualResult"] == "Test was skipped"


def test_a_case_without_steps_has_no_step_results():
    assert zephyr_reporter.step_results([], "Pass", None, None) == []


def test_every_assertion_message_hint_points_at_a_step_that_exists():
    """Each hint's step text appears in at least one defined case, so a hint can't silently go stale."""
    all_expected = " | ".join(e.lower() for case in zephyr_cases.CASES.values() for _, e in case.steps)
    stale = [h for _, h in zephyr_cases.FAILURE_HINTS if h not in all_expected]
    assert stale == []
