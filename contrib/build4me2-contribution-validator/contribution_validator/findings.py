"""Machine-readable results produced by contribution validation."""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class ValidationFinding:
    """One reason a contribution failed a check.

    ``code`` is a stable, machine-readable identifier (see
    :class:`FindingCode`). ``tensor_name`` is ``None`` for findings that apply to
    the whole contribution. ``details`` carries the measured values that
    triggered the finding, so a reviewer or a log sink can see the evidence
    without re-running the check.
    """

    code: str
    message: str
    tensor_name: str | None = None
    details: dict[str, Any] = field(default_factory=dict)


class FindingCode:  # pylint: disable=too-few-public-methods
    """Stable identifiers for the checks the validator performs."""

    BASE_FINGERPRINT_MISSING = "base-fingerprint-missing"
    BASE_FINGERPRINT_MISMATCH = "base-fingerprint-mismatch"
    MISSING_PARAMETER = "missing-parameter"
    UNEXPECTED_PARAMETER = "unexpected-parameter"
    NOT_A_TENSOR = "not-a-tensor"
    SHAPE_MISMATCH = "shape-mismatch"
    DEVICE_MISMATCH = "device-mismatch"
    DTYPE_MISMATCH = "dtype-mismatch"
    NON_FINITE = "non-finite"
    CAST_OVERFLOW = "value-overflows-base-dtype"
    STATISTIC_OVERFLOW = "update-not-measurable"
    LAYER_UPDATE_TOO_LARGE = "layer-update-too-large"
    LAYER_RELATIVE_UPDATE_TOO_LARGE = "layer-relative-update-too-large"
    ABS_DELTA_TOO_LARGE = "abs-delta-too-large"
    GLOBAL_UPDATE_TOO_LARGE = "global-update-too-large"
    GLOBAL_RELATIVE_UPDATE_TOO_LARGE = "global-relative-update-too-large"


@dataclass(frozen=True)
class TensorUpdateStats:  # pylint: disable=too-many-instance-attributes
    """Update statistics for one tensor, measured against the shared base.

    Statistics cover elements where both the base and the contributed value are
    finite. ``non_finite_count`` is the number of contributed elements that are
    NaN or infinite where the base holds a different value; a non-zero count
    always accompanies a ``non-finite`` finding. ``relative_l2`` is ``None``
    when the base tensor is all zeros, because a ratio would be meaningless.
    """

    name: str
    shape: tuple[int, ...]
    dtype: str
    numel: int
    base_l2: float
    delta_l2: float
    relative_l2: float | None
    max_abs_delta: float
    non_finite_count: int


@dataclass(frozen=True)
class GlobalUpdateStats:  # pylint: disable=too-many-instance-attributes
    """Update statistics aggregated across every comparable tensor.

    ``compared_tensor_count`` can be lower than ``expected_tensor_count`` when
    some tensors were missing or had incompatible shapes; those tensors cannot
    be compared and are reported as findings instead.
    """

    expected_tensor_count: int
    compared_tensor_count: int
    numel: int
    base_l2: float
    delta_l2: float
    relative_l2: float | None
    max_abs_delta: float
    non_finite_count: int


@dataclass(frozen=True)
class ContributionValidationReport:
    """Outcome of validating one contribution against the shared base."""

    node_id: str
    round_num: int
    accepted: bool
    findings: tuple[ValidationFinding, ...]
    layer_stats: dict[str, TensorUpdateStats]
    global_stats: GlobalUpdateStats

    @property
    def finding_codes(self) -> tuple[str, ...]:
        """Codes of all findings, in check order."""
        return tuple(finding.code for finding in self.findings)

    def to_dict(self) -> dict[str, Any]:
        """Return a strict-JSON-serializable representation of the report.

        Non-finite floats (only possible after an ``update-not-measurable``
        finding) are emitted as ``null`` so the output never contains NaN or
        Infinity tokens.
        """
        return _json_safe(
            {
                "node_id": self.node_id,
                "round_num": self.round_num,
                "accepted": self.accepted,
                "findings": [asdict(finding) for finding in self.findings],
                "layer_stats": {name: asdict(stats) for name, stats in self.layer_stats.items()},
                "global_stats": asdict(self.global_stats),
            }
        )


def _json_safe(value: Any) -> Any:
    """Recursively replace non-finite floats with ``None``."""
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    return value
