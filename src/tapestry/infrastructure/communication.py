"""Inter-node communication checks for consortium-training planning."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class CommunicationTopology(str, Enum):
    """Supported high-level topology choices."""

    HUB_AND_SPOKE = "hub-and-spoke"
    PEER_TO_PEER = "peer-to-peer"
    HYBRID = "hybrid"


class TransportProtocol(str, Enum):
    """Transport protocols under consideration for node communication."""

    GRPC_HTTP2 = "grpc-http2"
    HTTPS = "https"
    CUSTOM = "custom"


class CommunicationSeverity(str, Enum):
    """Severity for communication-plan findings."""

    BLOCKER = "blocker"
    WARNING = "warning"


@dataclass(frozen=True)
class CommunicationFinding:
    """One finding about a proposed communication plan."""

    requirement_id: str
    severity: CommunicationSeverity
    message: str


@dataclass(frozen=True)
# pylint: disable=too-many-instance-attributes
class CommunicationPlan:
    """A small, implementation-neutral description of M1 node communication."""

    topology: CommunicationTopology | str
    protocol: TransportProtocol | str
    sovereign_nodes_connect_outbound: bool
    authenticated_transport: bool
    coordinator_state_persistent: bool
    node_supervisor_with_backoff: bool
    membership_controls: bool
    straggler_policy: str | None = None
    notes: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        object.__setattr__(self, "topology", CommunicationTopology(self.topology))
        object.__setattr__(self, "protocol", TransportProtocol(self.protocol))
        if self.straggler_policy is not None and not self.straggler_policy.strip():
            raise ValueError("straggler_policy must not be blank when provided")
        object.__setattr__(self, "notes", tuple(self.notes))

    @property
    def has_no_blockers(self) -> bool:
        """Return whether assessment found no blocking issues."""
        return not any(finding.severity is CommunicationSeverity.BLOCKER for finding in assess_communication_plan(self))


def assess_communication_plan(plan: CommunicationPlan) -> tuple[CommunicationFinding, ...]:
    """Assess a communication plan against M1 consortium-readiness concerns."""
    findings: list[CommunicationFinding] = []

    if plan.topology is CommunicationTopology.PEER_TO_PEER:
        findings.append(
            CommunicationFinding(
                "COMM-TOPOLOGY",
                CommunicationSeverity.WARNING,
                "peer-to-peer adds coordination and firewall complexity; document why hub-and-spoke is insufficient",
            )
        )

    if not plan.sovereign_nodes_connect_outbound:
        findings.append(
            CommunicationFinding(
                "COMM-EGRESS",
                CommunicationSeverity.BLOCKER,
                "sovereign nodes should be able to participate with outbound-only connections",
            )
        )

    if not plan.authenticated_transport:
        findings.append(
            CommunicationFinding(
                "COMM-AUTH",
                CommunicationSeverity.BLOCKER,
                "transport must authenticate nodes before model updates or artifacts move",
            )
        )

    if not plan.coordinator_state_persistent:
        findings.append(
            CommunicationFinding(
                "COMM-STATE",
                CommunicationSeverity.WARNING,
                "coordinator state persistence should be verified before multi-day M1 runs",
            )
        )

    if not plan.node_supervisor_with_backoff:
        findings.append(
            CommunicationFinding(
                "COMM-SUPERVISION",
                CommunicationSeverity.WARNING,
                "node processes need supervisor/backoff behavior when the coordinator is unreachable",
            )
        )

    if not plan.membership_controls:
        findings.append(
            CommunicationFinding(
                "COMM-MEMBERSHIP",
                CommunicationSeverity.WARNING,
                "M1 governance needs explicit node join, leave, and eject controls",
            )
        )

    if plan.straggler_policy is None:
        findings.append(
            CommunicationFinding(
                "COMM-STRAGGLERS",
                CommunicationSeverity.WARNING,
                "heterogeneous nodes need a timeout or partial-aggregation policy",
            )
        )

    return tuple(findings)
