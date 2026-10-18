import pytest

from framework.exceptions import FrameworkException
from framework.test_data_loader import TestDataLoader

pytestmark = pytest.mark.unit


def test_resolves_env_placeholders():
    fake = {"TEST_USERNAME": "alice", "TEST_PASSWORD": "s3cr=t$1\\x"}
    creds = TestDataLoader("qa").node("credentials", fake.get)
    assert creds["username"] == "alice"
    assert creds["password"] == "s3cr=t$1\\x"  # regex-special chars survive


def test_missing_env_var_fails_with_variable_name():
    with pytest.raises(FrameworkException) as e:
        TestDataLoader("qa").node("credentials", lambda k: None)
    assert "TEST_USERNAME" in str(e.value)


def test_empty_env_var_is_treated_as_missing():
    with pytest.raises(FrameworkException):
        TestDataLoader("qa").node("credentials", lambda k: "")


def test_unknown_key_and_unknown_env_are_rejected():
    with pytest.raises(FrameworkException):
        TestDataLoader("qa").node("nope")
    with pytest.raises(FrameworkException):
        TestDataLoader("nonexistent-env")


def test_nodes_without_placeholders_need_no_environment():
    assert len(TestDataLoader("qa").node("invalidLocators", lambda k: None)) == 5


def test_node_returns_a_copy():
    loader = TestDataLoader("qa")
    loader.node("invalidLogin")["username"] = "changed"
    assert loader.node("invalidLogin")["username"] == "9000000000"
