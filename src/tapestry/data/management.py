"""Data-management capability checks for M1 planning."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class DataParticipationMode(str, Enum):
    """Dataset participation modes used by Tapestry governance requirements."""

    OPEN = "open"
    RESTRICTED = "restricted"
    LOCAL_ONLY = "local-only"
    PARTICIPANT_PRIVATE = "participant-private"


class DataPipelineCapability(str, Enum):
    """Capabilities required from data storage and processing pipelines."""

    CATALOG = "catalog"
    POINTER_BASED_DATASETS = "pointer-based-datasets"
    STRUCTURED_RIGHTS_METADATA = "structured-rights-metadata"
    ACCESS_CONTROL = "access-control"
    EVENT_CAPTURE = "event-capture"
    VISIBILITY_TIERS = "visibility-tiers"
    PORTABLE_SCHEMAS = "portable-schemas"
    STREAMING_LARGE_ARTIFACTS = "streaming-large-artifacts"


M1_REQUIRED_DATA_CAPABILITIES: frozenset[DataPipelineCapability] = frozenset(
    {
        DataPipelineCapability.CATALOG,
        DataPipelineCapability.POINTER_BASED_DATASETS,
        DataPipelineCapability.STRUCTURED_RIGHTS_METADATA,
        DataPipelineCapability.ACCESS_CONTROL,
        DataPipelineCapability.EVENT_CAPTURE,
        DataPipelineCapability.VISIBILITY_TIERS,
        DataPipelineCapability.PORTABLE_SCHEMAS,
    }
)


@dataclass(frozen=True)
class DataCapabilityFinding:
    """One missing capability from a data-management tool or plan."""

    capability: DataPipelineCapability
    message: str


@dataclass(frozen=True)
class DataToolAssessment:
    """A tool-neutral assessment of a data platform option such as ODS."""

    tool_name: str
    supported_capabilities: frozenset[DataPipelineCapability]
    viable_long_term: bool | None = None
    notes: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not self.tool_name.strip():
            raise ValueError("tool_name must not be empty")
        object.__setattr__(
            self,
            "supported_capabilities",
            frozenset(DataPipelineCapability(capability) for capability in self.supported_capabilities),
        )
        object.__setattr__(self, "notes", tuple(self.notes))

    @property
    def missing_m1_capabilities(self) -> tuple[DataPipelineCapability, ...]:
        """Capabilities still missing for M1 data-pipeline readiness."""
        return tuple(
            capability
            for capability in sorted(M1_REQUIRED_DATA_CAPABILITIES, key=lambda item: item.value)
            if capability not in self.supported_capabilities
        )

    def findings(self) -> tuple[DataCapabilityFinding, ...]:
        """Return capability gaps as reviewer-readable findings."""
        return tuple(
            DataCapabilityFinding(
                capability=capability,
                message=f"{self.tool_name} has not shown M1 capability: {capability.value}",
            )
            for capability in self.missing_m1_capabilities
        )


def ods_assessment_questions() -> tuple[str, ...]:
    """Questions to answer before adopting Open Data Spaces for Tapestry."""
    return (
        "Is the project active enough for Tapestry to depend on it?",
        "Can it stream large training artifacts without unacceptable overhead?",
        "Which governance controls are native and which require extensions?",
        "Can participant-local datasets be represented by manifests, hashes, or attestations?",
        "Can visibility-tiered evidence be exported for evaluation and certification gates?",
    )


def allowed_modes_for_shared_training() -> frozenset[DataParticipationMode]:
    """Return modes that can participate in shared training with controls."""
    return frozenset(
        {
            DataParticipationMode.OPEN,
            DataParticipationMode.RESTRICTED,
            DataParticipationMode.LOCAL_ONLY,
        }
    )
