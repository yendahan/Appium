from pathlib import Path

import pytest

from framework import mobile_actions
from framework.config_manager import ConfigManager
from framework.mobile_actions import MobileActions, folder_parts, set_screenshot_subfolder

pytestmark = pytest.mark.unit


class FakeDriver:
    def get_screenshot_as_png(self):
        return b"png"


@pytest.fixture(autouse=True)
def clean_subfolder():
    set_screenshot_subfolder("")
    yield
    set_screenshot_subfolder("")


def actions(tmp_path, folder=None):
    overrides = {"artifacts.dir": str(tmp_path)}
    if folder is not None:
        overrides["zephyr.cases.folder"] = folder
    return MobileActions(FakeDriver(), ConfigManager("qa", "emulator", overrides))


def relative(path: Path, tmp_path) -> str:
    return "/".join(path.relative_to(tmp_path).parts)


def test_the_folder_you_set_then_the_project_folders_then_the_run_then_the_result_folder(tmp_path):
    set_screenshot_subfolder("Android/Upgraded Consumer Account")
    shot = actions(tmp_path, "Regression").screenshot("test_login", "PASSED")
    assert relative(shot.parent, tmp_path) == (
        f"Screenshots/Regression/Android/Upgraded Consumer Account/{mobile_actions.RUN_FOLDER}/PASSED")
    assert shot.read_bytes() == b"png" and shot.name.startswith("test_login-")


def test_without_a_folder_set_that_level_is_left_out(tmp_path):
    set_screenshot_subfolder("Android/Upgraded Consumer Account")
    shot = actions(tmp_path).screenshot("t", "FAILED")
    assert relative(shot.parent, tmp_path) == (
        f"Screenshots/Android/Upgraded Consumer Account/{mobile_actions.RUN_FOLDER}/FAILED")


def test_a_parent_child_folder_value_makes_nested_folders(tmp_path):
    set_screenshot_subfolder("Android")
    shot = actions(tmp_path, "Sprint 42/Regression").screenshot("t", "RECEIPT")
    assert relative(shot.parent, tmp_path) == f"Screenshots/Sprint 42/Regression/Android/{mobile_actions.RUN_FOLDER}/RECEIPT"


def test_a_screenshot_with_no_test_context_still_saves(tmp_path):
    shot = actions(tmp_path, "Regression").screenshot("t")
    assert relative(shot.parent, tmp_path) == f"Screenshots/Regression/{mobile_actions.RUN_FOLDER}"


def test_spaces_are_kept_and_illegal_characters_and_dot_parts_are_dropped():
    assert folder_parts("Upgraded Consumer Account") == ["Upgraded Consumer Account"]
    assert folder_parts("a:b/c*d?") == ["a_b", "c_d_"]
    assert folder_parts("../../etc/./x") == ["etc", "x"]
    assert folder_parts("  //  ") == [] and folder_parts(None) == []


def test_a_folder_value_cannot_point_outside_the_Screenshots_folder(tmp_path):
    shot = actions(tmp_path, "../../outside").screenshot("t", "PASSED")
    assert tmp_path in shot.parents and "outside" in shot.parts
