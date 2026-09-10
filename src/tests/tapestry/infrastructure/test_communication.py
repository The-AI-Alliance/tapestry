"""Tests for inter-node communication planning checks."""

from __future__ import annotations

import unittest

from tapestry.infrastructure import (
    CommunicationPlan,
    CommunicationSeverity,
    CommunicationTopology,
    TransportProtocol,
    assess_communication_plan,
)


class CommunicationPlanTest(unittest.TestCase):
    """M1 communication-readiness checks."""

    def test_flower_style_hub_and_spoke_plan_has_no_blockers(self) -> None:
        """A managed hub-and-spoke transport plan has no readiness findings."""
        plan = CommunicationPlan(
            topology=CommunicationTopology.HUB_AND_SPOKE,
            protocol=TransportProtocol.GRPC_HTTP2,
            sovereign_nodes_connect_outbound=True,
            authenticated_transport=True,
            coordinator_state_persistent=True,
            node_supervisor_with_backoff=True,
            membership_controls=True,
            straggler_policy="round timeout with partial aggregation review",
        )

        self.assertEqual(assess_communication_plan(plan), ())
        self.assertTrue(plan.has_no_blockers)

    def test_missing_auth_and_outbound_participation_are_blockers(self) -> None:
        """Missing outbound participation and authentication are blockers."""
        plan = CommunicationPlan(
            topology=CommunicationTopology.HUB_AND_SPOKE,
            protocol=TransportProtocol.GRPC_HTTP2,
            sovereign_nodes_connect_outbound=False,
            authenticated_transport=False,
            coordinator_state_persistent=True,
            node_supervisor_with_backoff=True,
            membership_controls=True,
            straggler_policy="timeout",
        )

        findings = assess_communication_plan(plan)

        self.assertFalse(plan.has_no_blockers)
        self.assertEqual(
            [finding.requirement_id for finding in findings],
            ["COMM-EGRESS", "COMM-AUTH"],
        )
        self.assertTrue(all(finding.severity is CommunicationSeverity.BLOCKER for finding in findings))

    def test_peer_to_peer_without_operational_controls_warns(self) -> None:
        """Peer-to-peer plans without operational controls stay warnings-only."""
        plan = CommunicationPlan(
            topology=CommunicationTopology.PEER_TO_PEER,
            protocol=TransportProtocol.CUSTOM,
            sovereign_nodes_connect_outbound=True,
            authenticated_transport=True,
            coordinator_state_persistent=False,
            node_supervisor_with_backoff=False,
            membership_controls=False,
        )

        findings = assess_communication_plan(plan)

        self.assertTrue(plan.has_no_blockers)
        self.assertEqual(
            [finding.requirement_id for finding in findings],
            [
                "COMM-TOPOLOGY",
                "COMM-STATE",
                "COMM-SUPERVISION",
                "COMM-MEMBERSHIP",
                "COMM-STRAGGLERS",
            ],
        )


if __name__ == "__main__":
    unittest.main()
