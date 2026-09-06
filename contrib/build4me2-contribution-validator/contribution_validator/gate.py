"""Example wiring: a coordinator that validates contributions before merging.

This subclass shows where the validator would sit in
``tapestry.training.consortium.coordinator.ConsortiumCoordinator.run_round``.
It repeats the small amount of round bookkeeping from the parent so that the
core package stays untouched while the contract is reviewed. If the validator
is promoted, the same checks become a few lines inside ``run_round`` and this
module goes away.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

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


class ValidatingConsortiumCoordinator(ConsortiumCoordinator):
    """Coordinator that admits only validated contributions to the outer merge.

    Nodes whose contribution fails validation never reach the contribution
    policy or the merge. They appear in ``ConsortiumRoundResult.rejected_nodes``
    alongside policy rejections; ``round_summaries`` tells the two apart and
    keeps every per-node report so acceptance is recorded and repeatable.

    ``min_admitted_nodes`` is a quorum. Validation rejections shrink the set of
    nodes the policy weights, and ``ContributionPolicy.max_node_weight`` is
    renormalised over that set, so a lone survivor would otherwise receive the
    full weight. When fewer nodes than the quorum survive validation, the round
    does not touch the shared base.

    Summaries accumulate for the life of the coordinator. Long runs should
    persist and drop them periodically.
    """

    def __init__(
        self,
        base_model: nn.Module,
        contribution_policy: ContributionPolicy | None = None,
        outer_merge: OuterMerge | None = None,
        limits: ValidationLimits | None = None,
        min_admitted_nodes: int = 1,
    ) -> None:
        super().__init__(base_model, contribution_policy, outer_merge)
        if min_admitted_nodes < 1:
            raise ValueError("min_admitted_nodes must be at least 1")
        self.limits = limits or ValidationLimits()
        self.min_admitted_nodes = min_admitted_nodes
        self.round_summaries: dict[int, GateRoundSummary] = {}

    @property
    def validation_reports(self) -> dict[int, dict[str, ContributionValidationReport]]:
        """Per-round, per-node validation reports."""
        return {round_num: summary.reports for round_num, summary in self.round_summaries.items()}

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
        self.round_summaries[self._round] = GateRoundSummary(
            round_num=self._round,
            base_fingerprint=validator.reference_fingerprint,
            validation_rejected_nodes=[c.node_id for c in contributions if not reports[c.node_id].accepted],
            admitted_nodes=[contribution.node_id for contribution in admitted],
            quorum_met=quorum_met,
            min_admitted_nodes=self.min_admitted_nodes,
            reports=reports,
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
