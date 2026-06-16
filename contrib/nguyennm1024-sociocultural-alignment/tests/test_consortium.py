"""Smoke tests for the consortium-learning interface (no GPU/models needed)."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))


def test_member_defaults():
    from consortium import Member

    m = Member("/some/model")
    assert m.path == "/some/model"
    assert m.weight == 1.0
    assert m.name == ""


def test_consortium_method_is_abstract():
    import pytest

    from consortium import ConsortiumMethod

    with pytest.raises(TypeError):  # abstract: combine() is not implemented
        ConsortiumMethod()


def test_soup_is_a_consortium_method():
    import pytest

    pytest.importorskip("torch")  # the soup implementation pulls torch/transformers
    from consortium import ConsortiumMethod
    from consortium.soup import Soup

    assert issubclass(Soup, ConsortiumMethod)
    assert callable(getattr(Soup, "combine", None))
