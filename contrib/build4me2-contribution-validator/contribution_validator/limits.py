"""Configurable limits for contribution admission checks."""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum
from fnmatch import fnmatchcase


class DtypePolicy(str, Enum):
    """How strictly a contributed tensor's dtype must match the shared base."""

    EXACT = "exact"
    FLOAT_COMPATIBLE = "float-compatible"


class FingerprintPolicy(str, Enum):
    """Whether a contribution must declare the fingerprint of the base it trained from.

    ``IF_PRESENT`` checks a declared fingerprint but accepts contributions that
    declare none. ``REQUIRE`` rejects contributions without one. ``IGNORE``
    skips the check entirely.
    """

    IF_PRESENT = "if-present"
    REQUIRE = "require"
    IGNORE = "ignore"


@dataclass(frozen=True)
class ValidationLimits:  # pylint: disable=too-many-instance-attributes
    """Thresholds applied by :class:`~contribution_validator.ContributionValidator`.

    Every magnitude limit is optional. ``None`` disables that check, so the
    default configuration only enforces the structural contract: full parameter
    coverage, matching shapes, matching dtypes, and finite values.

    ``fingerprint_policy`` controls the base-checkpoint fingerprint check; see
    :class:`FingerprintPolicy`. ``dtype_policy`` controls dtype matching. ``EXACT`` requires the contributed
    dtype to equal the shared-base dtype. ``FLOAT_COMPATIBLE`` lets any floating
    point dtype stand in for a floating point base tensor (for example a node
    that trains in ``bfloat16`` against a ``float32`` base). Non-floating tensors
    such as integer buffers must always match exactly.

    Magnitude limits compare the contribution against the shared base the node
    started from. "Update" means ``contribution - base``. Norms are L2 norms
    computed in float64.

    - ``max_layer_update_norm``: per-tensor L2 norm of the update.
    - ``max_layer_relative_update``: per-tensor update norm divided by the base
      tensor norm.
    - ``max_abs_delta``: largest absolute change to any single parameter.
    - ``max_global_update_norm``: L2 norm of the update across all tensors.
    - ``max_global_relative_update``: global update norm divided by the global
      base norm.
    - ``layer_relative_update_groups``: ordered ``(pattern, limit)`` overrides
      for ``max_layer_relative_update``. An exact tensor name wins over any
      pattern. Otherwise the first matching pattern in tuple order applies, and
      unmatched tensors fall back to ``max_layer_relative_update``. Patterns are
      case-sensitive ``fnmatch`` patterns, and ``*`` also matches ``.``. A
      matching rule replaces the single value for that tensor, so it can loosen
      or tighten the limit.
    """

    dtype_policy: DtypePolicy | str = DtypePolicy.EXACT
    fingerprint_policy: FingerprintPolicy | str = FingerprintPolicy.IF_PRESENT
    max_layer_update_norm: float | None = None
    max_layer_relative_update: float | None = None
    max_abs_delta: float | None = None
    max_global_update_norm: float | None = None
    max_global_relative_update: float | None = None
    layer_relative_update_groups: tuple[tuple[str, float], ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "dtype_policy", DtypePolicy(self.dtype_policy))
        object.__setattr__(self, "fingerprint_policy", FingerprintPolicy(self.fingerprint_policy))
        for field_name in (
            "max_layer_update_norm",
            "max_layer_relative_update",
            "max_abs_delta",
            "max_global_update_norm",
            "max_global_relative_update",
        ):
            value = getattr(self, field_name)
            if value is None:
                continue
            if math.isnan(value) or value < 0.0:
                raise ValueError(f"{field_name} must be a non-negative number or None, got {value!r}")

        groups: list[tuple[str, float]] = []
        for group in self.layer_relative_update_groups:
            if not isinstance(group, (tuple, list)) or len(group) != 2:
                raise ValueError("each layer_relative_update_groups entry must be a (pattern, limit) pair")
            pattern, limit = group
            if not isinstance(pattern, str) or not pattern:
                raise ValueError(f"layer_relative_update_groups pattern must be a non-empty string, got {pattern!r}")
            if math.isnan(limit) or limit < 0.0:
                raise ValueError(
                    f"layer_relative_update_groups limit for {pattern!r} must be a non-negative number, "
                    f"got {limit!r}"
                )
            groups.append((pattern, float(limit)))
        object.__setattr__(self, "layer_relative_update_groups", tuple(groups))

    def layer_relative_update_limit(self, tensor_name: str) -> tuple[float | None, str | None]:
        """Return the relative-update limit for ``tensor_name`` and the matched rule.

        Exact tensor names are checked before patterns. Patterns are checked in
        tuple order with case-sensitive ``fnmatchcase`` semantics. Unmatched
        tensors use ``max_layer_relative_update`` and return ``None`` for the
        pattern.
        """
        for pattern, limit in self.layer_relative_update_groups:
            if pattern == tensor_name:
                return limit, pattern
        for pattern, limit in self.layer_relative_update_groups:
            if fnmatchcase(tensor_name, pattern):
                return limit, pattern
        return self.max_layer_relative_update, None
