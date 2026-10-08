"""Example wiring: a coordinator that validates contributions before merging.

This subclass shows where the validator would sit in
``tapestry.training.consortium.coordinator.ConsortiumCoordinator.run_round``.
It repeats the small amount of round bookkeeping from the parent so that the
core package stays untouched while the contract is reviewed. If the validator
is promoted, the same checks become a few lines inside ``run_round`` and this
module goes away.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
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

    Each round's summary is stored, old rounds beyond ``retain_rounds`` are
    evicted, and the summary is then handed to ``summary_sink``, so a caller
    can write it to an audit log and keep the record beyond the life of the
    coordinator. Both options default to the original behaviour: nothing is
    written anywhere and every summary is kept, which is fine for short runs
    but grows without limit over a long one, because each summary holds a
    report per node and per-tensor statistics within each report.
    """

    def __init__(  # pylint: disable=too-many-arguments,too-many-positional-arguments
        self,
        base_model: nn.Module,
        contribution_policy: ContributionPolicy | None = None,
        outer_merge: OuterMerge | None = None,
        limits: ValidationLimits | None = None,
        min_admitted_nodes: int = 1,
        summary_sink: Callable[[GateRoundSummary], None] | None = None,
        retain_rounds: int | None = None,
    ) -> None:
        super().__init__(base_model, contribution_policy, outer_merge)
        if min_admitted_nodes < 1:
            raise ValueError("min_admitted_nodes must be at least 1")
        self.limits = limits or ValidationLimits()
        self.min_admitted_nodes = min_admitted_nodes
        self.summary_sink = summary_sink
        self.retain_rounds = retain_rounds
        self.round_summaries: dict[int, GateRoundSummary] = {}

    @property
    def retain_rounds(self) -> int | None:
        """How many recent round summaries to keep, or ``None`` to keep every one."""
        return self._retain_rounds

    @retain_rounds.setter
    def retain_rounds(self, value: int | None) -> None:
        """Reject limits below one on every assignment, since they would disable eviction."""
        if value is not None and value < 1:
            raise ValueError("retain_rounds must be at least 1, or None to keep every round")
        self._retain_rounds = value

    @property
    def validation_reports(self) -> dict[int, dict[str, ContributionValidationReport]]:
        """Per-round, per-node validation reports still held in memory."""
        return {round_num: summary.reports for round_num, summary in self.round_summaries.items()}

    def _record(self, summary: GateRoundSummary) -> None:
        """Store a summary, evict any beyond the retention limit, then hand it to the sink.

        Storing first means a sink that raises does not also destroy the
        in-memory record, so the caller can repair the sink and write it. The
        summary just stored is the newest, so eviction never removes the one
        the sink is about to receive.

        The summary records what the gate decided about the contributions. It
        is written before the outer merge runs, so it does not assert that the
        merge succeeded.
        """
        self.round_summaries[summary.round_num] = summary
        if self.retain_rounds is not None:
            excess = len(self.round_summaries) - self.retain_rounds
            for round_num in sorted(self.round_summaries)[: max(excess, 0)]:
                del self.round_summaries[round_num]
        if self.summary_sink is not None:
            self.summary_sink(summary)

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
