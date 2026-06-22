"""Model soup -- v1 consortium method (weight-space averaging)."""
from ..base import ConsortiumMethod, Member
from .model_soup import average_weights


class Soup(ConsortiumMethod):
    """Weight-space averaging of same-base members: out = sum(w_i * member_i)."""

    name = "soup"

    def combine(self, members: list[Member], out_dir: str, **config) -> str:
        return average_weights(
            [m.path for m in members],
            [m.weight for m in members],
            out_dir,
        )


__all__ = ["Soup"]
