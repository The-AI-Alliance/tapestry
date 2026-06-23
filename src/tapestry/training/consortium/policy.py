"""Governed contribution policies for consortium training."""

from __future__ import annotations

from typing import Literal

ContributionWeighting = Literal["quality", "equal"]


class ContributionPolicy:  # pylint: disable=too-few-public-methods
    """Compute governed integration weights from contribution quality scores.

    The default ``quality`` policy is intentionally simple: reject contributions
    below a quality floor, then normalize quality scores while capping any one
    node's influence. The cap is an anti-capture control, not an optimizer trick.

    The ``equal`` policy supports the early-MVP comparison from issue #68:
    everyone who passes the quality floor receives equal influence, independent
    of quality score magnitude.
    """

    def __init__(
        self,
        quality_floor: float = 0.0,
        max_node_weight: float = 1.0,
        weighting: ContributionWeighting = "quality",
    ) -> None:
        if quality_floor < 0.0:
            raise ValueError("quality_floor must be non-negative")
        if not 0.0 < max_node_weight <= 1.0:
            raise ValueError("max_node_weight must be in (0, 1]")
        if weighting not in ("quality", "equal"):
            raise ValueError("weighting must be 'quality' or 'equal'")
        self.quality_floor = quality_floor
        self.max_node_weight = max_node_weight
        self.weighting = weighting

    def weights(self, quality_scores: dict[str, float]) -> dict[str, float]:
        """Return normalized contribution weights for accepted nodes."""
        accepted = {
            node_id: score for node_id, score in quality_scores.items() if score >= self.quality_floor and score > 0.0
        }
        if not accepted:
            return {}

        if self.weighting == "equal":
            equal_weight = 1.0 / len(accepted)
            return {node_id: equal_weight for node_id in accepted}

        weights = self._normalize(accepted)
        capped: dict[str, float] = {}
        remaining = dict(weights)
        remaining_mass = 1.0

        while remaining:
            over_cap = {
                node_id: weight
                for node_id, weight in remaining.items()
                if weight * remaining_mass > self.max_node_weight
            }
            if not over_cap:
                for node_id, weight in remaining.items():
                    capped[node_id] = weight * remaining_mass
                break

            for node_id in over_cap:
                capped[node_id] = self.max_node_weight
                remaining_mass -= self.max_node_weight
                remaining.pop(node_id)

            if not remaining:
                break
            remaining = self._normalize(remaining)

        # Floating point and repeated capping can leave tiny residue.
        total = sum(capped.values())
        if total > 0:
            capped = {node_id: weight / total for node_id, weight in capped.items()}
        return capped

    @staticmethod
    def _normalize(scores: dict[str, float]) -> dict[str, float]:
        total = sum(scores.values())
        return {node_id: score / total for node_id, score in scores.items()}
