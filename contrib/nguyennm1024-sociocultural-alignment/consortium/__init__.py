"""Consortium learning: fuse independently-trained member models into one.

Model soup (``consortium.soup``) is the v1 method. See ``consortium.base`` for the
``ConsortiumMethod`` contract that future methods implement.
"""
from .base import ConsortiumMethod, Member

__all__ = ["ConsortiumMethod", "Member"]
