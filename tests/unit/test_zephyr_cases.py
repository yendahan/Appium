import ast
from pathlib import Path

import pytest

from framework.zephyr_cases import CASES, case_for, folder_of, groups

pytestmark = pytest.mark.unit

DEVICE_TESTS = Path(__file__).resolve().parents[1] / "Android"


def _tests_with_zephyr_marker():
    found = set()
    for path in DEVICE_TESTS.rglob("test_*.py"):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.FunctionDef) and node.name.startswith("test_") and any(
                    "zephyr" in ast.dump(d) for d in node.decorator_list):
                found.add(f"{path.name}::{node.name}")
    return found


def test_every_zephyr_marked_test_has_a_case_definition_and_vice_versa():
    marked = _tests_with_zephyr_marker()
    assert marked == set(CASES), (f"marked but not defined: {sorted(marked - set(CASES))}; "
                                  f"defined but not marked: {sorted(set(CASES) - marked)}")


def test_case_names_are_unique_and_every_case_has_steps():
    names = [c.name for c in CASES.values()]
    assert len(names) == len(set(names))
    assert all(c.steps and c.objective for c in CASES.values())


def test_case_for_ignores_the_directory_and_the_parameters():
    expected = CASES["test_send_money.py::test_via_qr_valid"]
    assert case_for("tests/Android/Upgraded Consumer Account/test_send_money.py::test_via_qr_valid[QRP2P - Static]") is expected
    assert case_for("test_send_money.py::test_via_qr_valid") is expected
    assert case_for("tests/Android/Upgraded Consumer Account/test_nope.py::test_x") is None


def test_each_case_sits_in_the_zephyr_folder_of_its_test_file():
    assert folder_of("test_login.py::test_wrong_password_is_rejected") == "Android/Upgraded Consumer Account"
    assert folder_of("test_nope.py::test_x") == ""  # a file that does not exist under tests/ has no sub-folder


def test_all_cases_are_grouped_under_the_project_folders():
    grouped = groups()
    upgraded, asenso = "Android/Upgraded Consumer Account", "Android/Consumer Account with Asenso"
    account, basic = "Android/Asenso Account", "Android/Basic Account"
    assert set(grouped) == {upgraded, asenso, account, basic}
    assert len(grouped[upgraded]) == len(grouped[asenso])
    assert len(grouped[account]) == 5
    assert len(grouped[basic]) == 9  # 3 registration + upgrade, biometric login, add money (2), pay bills, transactions
    assert sum(len(v) for v in grouped.values()) == len(CASES)


def test_asenso_cases_mirror_the_upgraded_ones_with_prefixed_names():
    upgraded = CASES["test_login.py::test_wrong_password_is_rejected"]
    asenso = CASES["test_asenso_login.py::test_wrong_password_is_rejected"]
    assert asenso.name == f"Asenso {upgraded.name}" and asenso.steps == upgraded.steps
    assert folder_of("test_asenso_login.py::test_x") == "Android/Consumer Account with Asenso"
