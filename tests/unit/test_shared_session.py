import pytest

from framework.shared_session import SharedSession

pytestmark = pytest.mark.unit


class FakeDriver:
    def __init__(self):
        self.quit_called = False

    def quit(self):
        self.quit_called = True


def make(home=True):
    created = []

    def create():
        created.append(FakeDriver())
        return created[-1]

    return SharedSession(create, lambda drv: home), created


def test_same_account_reuses_the_session():
    shared, created = make()
    first = shared.acquire("credentials")
    assert shared.acquire("credentials") is first
    assert len(created) == 1


def test_other_account_closes_the_old_session_and_starts_a_new_one():
    shared, created = make()
    first = shared.acquire("credentials")
    second = shared.acquire("asensoCredentials")
    assert second is not first and first.quit_called


def test_session_that_cannot_get_home_is_replaced():
    shared, created = make(home=False)
    first = shared.acquire("credentials")
    assert shared.acquire("credentials") is not first and first.quit_called


def test_discard_quits_and_the_next_acquire_is_fresh():
    shared, created = make()
    first = shared.acquire("credentials")
    shared.discard()
    assert first.quit_called and not shared.owns(first)
    assert shared.acquire("credentials") is not first
