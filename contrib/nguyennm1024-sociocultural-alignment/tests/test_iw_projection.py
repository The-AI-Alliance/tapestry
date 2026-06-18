"""Smoke tests for the self-contained Inglehart-Welzel projector (no GPU/models/survey data)."""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "evaluation", "iw"))


def test_items_count():
    from iw_project import ITEMS

    assert len(ITEMS) == 10


def test_projection_returns_finite_xy():
    from iw_project import project

    # one plausible 10-item survey response vector
    x, y = project([2, 2, 2, 1, 8, 8, 7, 2, 3, 1])
    assert math.isfinite(float(x))
    assert math.isfinite(float(y))
