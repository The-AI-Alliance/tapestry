"""Example wiring: a coordinator that validates contributions before merging.

This subclass shows where the validator would sit in
``tapestry.training.consortium.coordinator.ConsortiumCoordinator.run_round``.
It repeats the small amount of round bookkeeping from the parent so that the
core package stays untouched while the contract is reviewed. If the validator
is promoted, the same checks become a few lines inside ``run_round`` and this
module goes away.
"""

from __future__ import annotations

import json
import os
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from torch import nn

from tapestry.training.consortium import (
    ConsortiumCoordinator,
    ConsortiumRoundResult,
    ContributionPolicy,
    OuterMerge,
    SovereignTrainingNode,
)

from .findings import ContributionValidationReport
from .limits import ValidationLimits
from .validator import ContributionValidator


@dataclass(frozen=True)
class GateRoundSummary:
    """What the validation gate decided in one round.

    ``ConsortiumRoundResult.rejected_nodes`` mixes nodes rejected here with
    nodes rejected by the contribution policy. This summary keeps the two
    apart, and records when a round was skipped because too few contributions
    survived validation to honour the policy's anti-capture cap.
    """

    round_num: int
    base_fingerprint: str
    validation_rejected_nodes: list[str]
    admitted_nodes: list[str]
    quorum_met: bool
    min_admitted_nodes: int
    reports: dict[str, ContributionValidationReport]

    def to_dict(self) -> dict[str, Any]:
        """Return a strict-JSON-serializable representation of the summary."""
        return {
            "round_num": self.round_num,
            "base_fingerprint": self.base_fingerprint,
            "validation_rejected_nodes": list(self.validation_rejected_nodes),
            "admitted_nodes": list(self.admitted_nodes),
            "quorum_met": self.quorum_met,
            "min_admitted_nodes": self.min_admitted_nodes,
            "reports": {node_id: report.to_dict() for node_id, report in self.reports.items()},
        }


def read_round_summaries(path: str | os.PathLike[str]) -> list[dict[str, Any]]:
    """Load the summaries a gate appended to ``path``, oldest round first."""
    with Path(path).open(encoding="utf-8") as summary_file:
        return [json.loads(line) for line in summary_file if line.strip()]


class ValidatingConsortiumCoordinator(ConsortiumCoordinator):
    """Coordinator that admits only validated contributions to the outer merge.

    Nodes whose contribution fails validation never reach the contribution
    policy or the merge. They appear in ``ConsortiumRoundResult.rejected_nodes``
    alongside policy rejections; ``last_summary`` tells the two apart and keeps
    every per-node report for the round just run.

    ``min_admitted_nodes`` is a quorum. Validation rejections shrink the set of
    nodes the policy weights, and ``ContributionPolicy.max_node_weight`` is
    renormalised over that set, so a lone survivor would otherwise receive the
    full weight. When fewer nodes than the quorum survive validation, the round
    does not touch the shared base.

    Only the latest summary is kept in memory. When ``summary_path`` is given,
    every round's summary is appended to that file as one line of JSON before
    the outer merge, so the full record lives on disk and can be loaded with
    ``read_round_summaries``. If the write fails, the round stops before the
    shared base changes, so no merged round goes unrecorded.
    """

    def __init__(  # pylint: disable=too-many-arguments,too-many-positional-arguments
        self,
        base_model: nn.Module,
        contribution_policy: ContributionPolicy | None = None,
        outer_merge: OuterMerge | None = None,
        limits: ValidationLimits | None = None,
        min_admitted_nodes: int = 1,
        summary_path: str | os.PathLike[str] | None = None,
    ) -> None:
        super().__init__(base_model, contribution_policy, outer_merge)
        if min_admitted_nodes < 1:
            raise ValueError("min_admitted_nodes must be at least 1")
        self.limits = limits or ValidationLimits()
        self.min_admitted_nodes = min_admitted_nodes
        self.summary_path = Path(summary_path) if summary_path is not None else None
        self.last_summary: GateRoundSummary | None = None

    def _record(self, summary: GateRoundSummary) -> None:
        """Keep the summary as ``last_summary`` and append it to ``summary_path``, if set.

        JSON Lines lets each round append one line instead of rewriting the
        whole file. The summary records what the gate decided; it is written
        before the outer merge, so it does not assert that the merge succeeded.
        """
        self.last_summary = summary
        if self.summary_path is not None:
            with self.summary_path.open("a", encoding="utf-8") as summary_file:
                summary_file.write(json.dumps(summary.to_dict()) + "\n")

    def run_round(self, nodes: Sequence[SovereignTrainingNode]) -> ConsortiumRoundResult:
        """Run one consortium cycle, validating each contribution before merge."""
        previous_state = self.shared_base_state
        validator = ContributionValidator(previous_state, self.limits)
        self._round += 1

        cycle_results = [node.run_sovereign_cycle(self._round, previous_state) for node in nodes]
        for result in cycle_results:
            self.sovereign_artifacts[result.artifact.node_id] = result.artifact

        contributions = [result.contribution for result in cycle_results]
        reports = {contribution.node_id: validator.validate(contribution) for contribution in contributions}
        admitted = [contribution for contribution in contributions if reports[contribution.node_id].accepted]
        quorum_met = len(admitted) >= self.min_admitted_nodes
        self._record(
            GateRoundSummary(
                round_num=self._round,
                base_fingerprint=validator.reference_fingerprint,
                validation_rejected_nodes=[c.node_id for c in contributions if not reports[c.node_id].accepted],
                admitted_nodes=[contribution.node_id for contribution in admitted],
                quorum_met=quorum_met,
                min_admitted_nodes=self.min_admitted_nodes,
                reports=reports,
            )
        )
        if not quorum_met:
            admitted = []

        weights = self.contribution_policy.weights(
            {contribution.node_id: contribution.quality_score for contribution in admitted}
        )
        accepted = list(weights)
        rejected = [contribution.node_id for contribution in contributions if contribution.node_id not in weights]

        if weights:
            local_states_by_node = {contribution.node_id: contribution.local_model_state for contribution in admitted}
            integrated_state = self.outer_merge.merge(previous_state, local_states_by_node, weights)
            self.base_model.load_state_dict(integrated_state)

        return ConsortiumRoundResult(
            round_num=self._round,
            previous_base_state=previous_state,
            shared_base_state=self.shared_base_state,
            accepted_nodes=accepted,
            rejected_nodes=rejected,
            contribution_weights=weights,
            outer_merge_strategy=self.outer_merge.strategy.value,
        )
