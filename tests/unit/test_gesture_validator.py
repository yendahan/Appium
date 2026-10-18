import math

import pytest

from framework import gesture_validator as gv

pytestmark = pytest.mark.unit


@pytest.mark.parametrize("p", [5e-324, 0.01, 0.5, 1.0])
def test_accepts_boundary_percents(p):
    assert gv.validate_percent(p) == p


@pytest.mark.parametrize("p", [0.0, -0.1, 1.0000001, math.nan, math.inf])
def test_rejects_out_of_range_percents(p):
    with pytest.raises(ValueError):
        gv.validate_percent(p)


def test_normalises_direction_case_and_whitespace():
    assert gv.validate_direction("  UP ") == "up"


@pytest.mark.parametrize("bad", [None, "", "diagonal"])
def test_rejects_bad_directions(bad):
    with pytest.raises(ValueError):
        gv.validate_direction(bad)


def test_max_attempts_boundary():
    assert gv.validate_max_attempts(1) == 1
    for bad in (0, -1):
        with pytest.raises(ValueError):
            gv.validate_max_attempts(bad)
