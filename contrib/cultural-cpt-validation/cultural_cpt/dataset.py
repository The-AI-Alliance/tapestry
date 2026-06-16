"""Real corpus loading, validation, and the EXP-001 scientific controls.

`corpora.py` holds the tiny placeholder text for smoke mode; this module is the
real-data path. When a run is given a ``--corpus-path``, every arm's text comes
through here, and it does not just *load* — it **enforces the controls the
experiment's validity depends on**:

1. **Permissive licensing** — every document declares a license, and only
   licenses on :data:`PERMISSIVE_LICENSES` are accepted, so the assembled corpus
   can live in (or be regenerated for) this open repo.
2. **WVS decontamination** (spec: "strip any WVS-resembling items ... or we
   measure memorization, not alignment") — documents whose text reproduces a
   survey/behavioral item stem or option are rejected before any CPT.
3. **Matched-twin control** (spec: "Arms 1 and 2 differ *only* in cultural
   grounding ... size, quality, recency, register held constant") — the
   ``grounded`` and ``language_matched`` corpora are checked against declared
   tolerances (same language, same register, comparable token budget). A corpus
   that silently breaks the twin invariant would invalidate the decisive
   ``grounded vs language_matched`` comparison, so we fail loudly instead.

On-disk layout (one directory per culture, pointed at by ``--corpus-path``)::

    <root>/
      manifest.json          # CorpusManifest: per-arm metadata + tolerances
      grounded.jsonl         # one DocumentRecord per line
      language_matched.jsonl
      grounded_translated.jsonl   # optional (Arm 3)

See ``data/README.md`` for the schema and the sourcing protocol.
"""

from __future__ import annotations

import hashlib
import json
import random
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Sequence

# --- Licensing ---------------------------------------------------------------

# Permissive / open licenses accepted for corpus documents. The user constraint
# for EXP-001 is "permissively-licensed only" so the data can live in this open
# (Apache-2.0 / CC-BY / CDLA) repository. Identifiers are SPDX where one exists;
# "public-domain"/"CC0-1.0" cover gazettes, treaties, and pre-modern texts.
PERMISSIVE_LICENSES: frozenset[str] = frozenset(
    {
        "public-domain",
        "cc0-1.0",
        "cc-by-4.0",
        "cc-by-3.0",
        "cc-by-2.0",
        "cc-by-sa-4.0",
        "cc-by-sa-3.0",
        "odc-by-1.0",
        "ogl-3.0",  # UK Open Government Licence; many gazettes use equivalents
        "apache-2.0",
        "mit",
    }
)


def normalize_license(value: str) -> str:
    """Canonicalize a license string for membership testing."""
    return value.strip().lower().replace(" ", "-")


# --- Document + manifest schema ---------------------------------------------


@dataclass(frozen=True)
class DocumentRecord:
    """One training document (one JSONL line) with its provenance.

    ``text`` is what gets continued-pretrained on; the rest is provenance the
    validators and the audit trail need: where it came from, under what license,
    in what language, which value-domain, and (for the recency control) when.
    """

    id: str
    text: str
    source: str
    license: str
    lang: str
    domain: str = ""
    url: str = ""
    year: int | None = None

    @classmethod
    def from_json(cls, obj: dict, *, where: str) -> "DocumentRecord":
        missing = [k for k in ("id", "text", "source", "license", "lang") if not obj.get(k)]
        if missing:
            raise CorpusError(f"{where}: document missing required field(s): {', '.join(missing)}")
        year = obj.get("year")
        if year is not None and not isinstance(year, int):
            raise CorpusError(f"{where}: 'year' must be an integer, got {year!r}")
        return cls(
            id=str(obj["id"]),
            text=str(obj["text"]),
            source=str(obj["source"]),
            license=str(obj["license"]),
            lang=str(obj["lang"]),
            domain=str(obj.get("domain", "")),
            url=str(obj.get("url", "")),
            year=year,
        )


@dataclass(frozen=True)
class ArmManifest:
    """Declared metadata for one arm's corpus, checked against its documents."""

    file: str
    lang: str
    register: str = ""  # e.g. "encyclopedic", "legal", "literary"
    domains: tuple[str, ...] = ()
    value_laden: bool | None = None  # grounded -> True, language_matched -> False
    min_year: int | None = None
    max_year: int | None = None


@dataclass(frozen=True)
class TwinTolerances:
    """How closely the grounded / language-matched twin must match.

    The matched-twin control: the two arms may differ in cultural grounding and
    nothing else. These bound the "nothing else".
    """

    token_ratio_tolerance: float = 0.20  # |1 - g/lm| must be <= this
    require_same_language: bool = True
    require_same_register: bool = True

    @classmethod
    def from_json(cls, obj: dict) -> "TwinTolerances":
        return cls(
            token_ratio_tolerance=float(obj.get("token_ratio_tolerance", 0.20)),
            require_same_language=bool(obj.get("require_same_language", True)),
            require_same_register=bool(obj.get("require_same_register", True)),
        )


@dataclass(frozen=True)
class CorpusManifest:
    """Parsed ``manifest.json`` for one culture's corpus root."""

    culture: str
    language: str
    arms: dict[str, ArmManifest]
    twin: TwinTolerances = field(default_factory=TwinTolerances)

    @classmethod
    def load(cls, root: Path) -> "CorpusManifest":
        path = root / "manifest.json"
        if not path.is_file():
            raise CorpusError(f"no manifest.json in corpus root {root}")
        try:
            obj = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise CorpusError(f"{path}: invalid JSON: {exc}") from exc
        if not obj.get("culture") or not obj.get("language"):
            raise CorpusError(f"{path}: manifest needs 'culture' and 'language'")
        arms_obj = obj.get("arms") or {}
        if not arms_obj:
            raise CorpusError(f"{path}: manifest declares no arms")
        arms: dict[str, ArmManifest] = {}
        for name, spec in arms_obj.items():
            if not spec.get("file"):
                raise CorpusError(f"{path}: arm {name!r} missing 'file'")
            arms[name] = ArmManifest(
                file=str(spec["file"]),
                lang=str(spec.get("lang", obj["language"])),
                register=str(spec.get("register", "")),
                domains=tuple(spec.get("domains", ()) or ()),
                value_laden=spec.get("value_laden"),
                min_year=spec.get("min_year"),
                max_year=spec.get("max_year"),
            )
        return cls(
            culture=str(obj["culture"]),
            language=str(obj["language"]),
            arms=arms,
            twin=TwinTolerances.from_json(obj.get("twin_matching", {})),
        )


class CorpusError(ValueError):
    """Raised when a corpus or manifest violates an EXP-001 validity constraint."""


# --- Decontamination ---------------------------------------------------------

_WORD_RE = re.compile(r"\w+", re.UNICODE)


def _normalize(text: str) -> list[str]:
    """Lowercase word tokens, script-agnostic (Unicode \\w)."""
    return _WORD_RE.findall(text.lower())


def wvs_probe_phrases(*, min_words: int = 5) -> tuple[str, ...]:
    """Collect WVS / behavioral item phrasings to screen corpora against.

    Pulls the stems, paraphrases, and option texts from the live instruments so
    decontamination tracks the actual battery instead of a stale copy. Only
    phrases of at least ``min_words`` tokens are kept — short option fragments
    ("It depends.") would false-positive on ordinary prose.
    """
    from . import wvs

    phrases: set[str] = set()
    item_sets: list[Sequence] = [wvs._ITEMS]
    try:  # behavioral probe shares the SurveyItem shape; include it if present
        from . import behavior

        for attr in ("_SCENARIOS", "_ITEMS", "_PROBES"):
            items = getattr(behavior, attr, None)
            if items:
                item_sets.append(items)
                break
    except Exception:  # pragma: no cover - behavior is optional for decontam
        pass

    for items in item_sets:
        for item in items:
            for stem in getattr(item, "stem_paraphrases", ()):
                phrases.add(stem)
            for opt in getattr(item, "options", ()):
                phrases.add(opt.text)

    return tuple(p for p in phrases if len(_normalize(p)) >= min_words)


@dataclass(frozen=True)
class Contamination:
    """A document flagged as reproducing a survey/behavioral item."""

    doc_id: str
    phrase: str
    jaccard: float


def find_contamination(
    docs: Iterable[DocumentRecord],
    probes: Sequence[str],
    *,
    max_jaccard: float = 0.6,
) -> list[Contamination]:
    """Flag documents that reproduce a WVS/behavioral item phrasing.

    Two detectors, both on Unicode-word tokens (so this works for non-Latin
    scripts): an exact normalized-substring match (verbatim leakage), and a
    sliding-window token Jaccard >= ``max_jaccard`` (near-duplicate / lightly
    edited leakage). Returns the worst hit per (document, probe).
    """
    norm_probes = [(p, _normalize(p)) for p in probes]
    norm_probes = [(p, toks) for p, toks in norm_probes if toks]
    flags: list[Contamination] = []
    for doc in docs:
        doc_toks = _normalize(doc.text)
        if not doc_toks:
            continue
        doc_join = " ".join(doc_toks)
        for phrase, ptoks in norm_probes:
            pjoin = " ".join(ptoks)
            if pjoin in doc_join:
                flags.append(Contamination(doc.id, phrase, 1.0))
                continue
            best = _max_window_jaccard(doc_toks, ptoks)
            if best >= max_jaccard:
                flags.append(Contamination(doc.id, phrase, round(best, 3)))
    return flags


def _max_window_jaccard(doc_toks: Sequence[str], probe_toks: Sequence[str]) -> float:
    """Max Jaccard between the probe's token set and any same-length window."""
    n = len(probe_toks)
    if n == 0 or len(doc_toks) < n:
        return 0.0
    pset = set(probe_toks)
    best = 0.0
    for i in range(0, len(doc_toks) - n + 1):
        wset = set(doc_toks[i : i + n])
        inter = len(pset & wset)
        union = len(pset | wset)
        if union:
            best = max(best, inter / union)
    return best


# --- Corpus resampling -------------------------------------------------------
#
# Run 5's headline effect did not survive a *fresh* corpus pull (Run 6): the
# real variance source is which documents land in the twin, not the (deterministic)
# training seed. To estimate that band honestly we resample the on-disk pool:
# each "draw" deterministically subsamples a fraction of each arm's documents,
# so the cross-draw spread of the decisive comparison is the genuine noise band.


def _stable_seed(sample_seed: int, arm: str) -> int:
    """A process-stable integer seed from (draw seed, arm).

    Uses SHA-256 rather than ``hash()`` so the selected subset is identical
    across processes/machines regardless of ``PYTHONHASHSEED`` — a corpus draw
    must reproduce exactly on the GPU box and in CI. The arm name is mixed in so
    the twin arms draw independent (but each individually reproducible) subsets.
    """
    digest = hashlib.sha256(f"{sample_seed}:{arm}".encode("utf-8")).hexdigest()
    return int(digest[:16], 16)


def subsample_documents(
    docs: Sequence[DocumentRecord],
    *,
    arm: str,
    fraction: float,
    sample_seed: int | None,
    target_tokens: float | None = None,
) -> list[DocumentRecord]:
    """Deterministically subsample one arm's documents for a corpus draw.

    ``fraction >= 1.0`` or ``sample_seed is None`` returns the full pool (the
    default, single-corpus behavior). Otherwise it keeps a random subset whose
    **token mass** is ~``fraction`` of the arm's pool, by shuffling documents
    with a process-stable seed and accumulating until the token budget is met.

    Sampling on *tokens* (not document count) keeps the draw representative, but
    when the full-pool twin ratio sits near the tolerance edge, shrinking each
    arm to a fraction of *its own* mass lets per-document granularity tip the
    draw's grounded/language ratio over tolerance. ``target_tokens`` overrides
    the per-arm ``fraction * total`` budget with an explicit common budget, which
    the twin loader uses to drive both arms to the *same* token mass per draw so
    the matched-twin invariant holds with margin. The per-arm controls and the
    twin check then run on the subsampled set, so we validate exactly what we train on.
    """
    if sample_seed is None or fraction >= 1.0:
        return list(docs)
    if fraction <= 0.0:
        raise CorpusError(f"arm {arm!r}: corpus sample fraction must be in (0, 1], got {fraction}")
    tokens = [len(_normalize(d.text)) for d in docs]
    total = sum(tokens)
    if total == 0:
        return list(docs)
    target = target_tokens if target_tokens is not None else fraction * total
    order = list(range(len(docs)))
    random.Random(_stable_seed(sample_seed, arm)).shuffle(order)
    picked: list[int] = []
    acc = 0
    for i in order:
        picked.append(i)
        acc += tokens[i]
        if acc >= target:
            break
    return [docs[i] for i in sorted(picked)]


# --- Loading + validation ----------------------------------------------------


def _read_jsonl(path: Path) -> list[DocumentRecord]:
    if not path.is_file():
        raise CorpusError(f"corpus file not found: {path}")
    docs: list[DocumentRecord] = []
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError as exc:
            raise CorpusError(f"{path}:{lineno}: invalid JSON: {exc}") from exc
        docs.append(DocumentRecord.from_json(obj, where=f"{path}:{lineno}"))
    if not docs:
        raise CorpusError(f"corpus file is empty: {path}")
    return docs


def _validate_arm(
    arm: str,
    spec: ArmManifest,
    docs: Sequence[DocumentRecord],
    *,
    decontaminate: bool,
    max_jaccard: float,
) -> None:
    """License, language, recency, and decontamination checks for one arm."""
    for doc in docs:
        lic = normalize_license(doc.license)
        if lic not in PERMISSIVE_LICENSES:
            raise CorpusError(
                f"arm {arm!r} doc {doc.id!r}: license {doc.license!r} is not in the "
                f"permissive allowlist (got normalized {lic!r}). EXP-001 corpora are "
                f"permissive-only; see PERMISSIVE_LICENSES."
            )
        if doc.lang.strip().lower() != spec.lang.strip().lower():
            raise CorpusError(f"arm {arm!r} doc {doc.id!r}: lang {doc.lang!r} != manifest arm lang {spec.lang!r}")
        if doc.year is not None:
            if spec.min_year is not None and doc.year < spec.min_year:
                raise CorpusError(f"arm {arm!r} doc {doc.id!r}: year {doc.year} < min_year {spec.min_year}")
            if spec.max_year is not None and doc.year > spec.max_year:
                raise CorpusError(f"arm {arm!r} doc {doc.id!r}: year {doc.year} > max_year {spec.max_year}")

    if decontaminate:
        flags = find_contamination(docs, wvs_probe_phrases(), max_jaccard=max_jaccard)
        if flags:
            head = "; ".join(f"{f.doc_id}~{f.phrase!r}(j={f.jaccard})" for f in flags[:3])
            raise CorpusError(
                f"arm {arm!r}: {len(flags)} document(s) reproduce WVS/behavioral items "
                f"(measuring memorization, not alignment). First: {head}. "
                f"Strip these from the corpus before training."
            )


def _token_count(docs: Sequence[DocumentRecord]) -> int:
    return sum(len(_normalize(d.text)) for d in docs)


def validate_twin(
    manifest: CorpusManifest,
    grounded: Sequence[DocumentRecord],
    language_matched: Sequence[DocumentRecord],
) -> None:
    """Enforce the matched-twin control between grounded and language_matched.

    They may differ in cultural grounding and nothing else. We check the levers
    most likely to silently confound the result: language, register, and token
    budget. ``value_laden`` is asserted to differ (grounded True, neutral False)
    so a mislabeled corpus can't pose as its own twin.
    """
    tol = manifest.twin
    g_spec, lm_spec = manifest.arms["grounded"], manifest.arms["language_matched"]

    if tol.require_same_language and g_spec.lang != lm_spec.lang:
        raise CorpusError(
            f"twin control: grounded lang {g_spec.lang!r} != language_matched lang "
            f"{lm_spec.lang!r}. The neutral twin must be the SAME language."
        )
    if tol.require_same_register and g_spec.register != lm_spec.register:
        raise CorpusError(
            f"twin control: grounded register {g_spec.register!r} != language_matched "
            f"register {lm_spec.register!r}. Hold register constant across the twin."
        )
    if g_spec.value_laden is False or lm_spec.value_laden is True:
        raise CorpusError(
            "twin control: expected grounded.value_laden=true and "
            "language_matched.value_laden=false in the manifest."
        )

    g_tokens, lm_tokens = _token_count(grounded), _token_count(language_matched)
    if g_tokens == 0 or lm_tokens == 0:
        raise CorpusError("twin control: a twin arm has zero tokens")
    ratio_dev = abs(1.0 - g_tokens / lm_tokens)
    if ratio_dev > tol.token_ratio_tolerance:
        raise CorpusError(
            f"twin control: token budgets differ by {ratio_dev:.0%} "
            f"(grounded={g_tokens}, language_matched={lm_tokens}); tolerance is "
            f"{tol.token_ratio_tolerance:.0%}. Match the corpus sizes."
        )


def declared_arms(root: Path | str) -> set[str]:
    """Arm names a real corpus root provides (e.g. minimal twin vs. all five)."""
    return set(CorpusManifest.load(Path(root)).arms)


def load_arm_documents(
    root: Path | str,
    arm: str,
    *,
    manifest: CorpusManifest | None = None,
    decontaminate: bool = True,
    max_jaccard: float = 0.6,
    check_twin: bool = True,
    sample_fraction: float = 1.0,
    sample_seed: int | None = None,
) -> list[DocumentRecord]:
    """Load and validate one arm's documents from a real corpus root.

    Runs the per-arm checks always, and the matched-twin check whenever the
    requested arm is part of the twin (``grounded``/``language_matched``) and
    its partner is present in the manifest.

    ``sample_fraction`` < 1 with a ``sample_seed`` selects one corpus *draw* — a
    deterministic subset of each arm's pool — so callers can resample the corpus
    to estimate the cross-corpus noise band. The validity controls and twin check
    run on the subsampled set; both twin arms are subsampled with the same draw
    seed so the matched-twin invariant is enforced per draw.
    """
    root = Path(root)
    manifest = manifest or CorpusManifest.load(root)
    if arm not in manifest.arms:
        raise CorpusError(f"arm {arm!r} not in manifest for {root} (declared: {sorted(manifest.arms)})")
    spec = manifest.arms[arm]
    raw = _read_jsonl(root / spec.file)

    is_twin = arm in ("grounded", "language_matched") and {"grounded", "language_matched"} <= set(manifest.arms)
    resampling = sample_seed is not None and sample_fraction < 1.0
    need_partner = is_twin and (check_twin or resampling)
    partner = "language_matched" if arm == "grounded" else "grounded"
    partner_raw = _read_jsonl(root / manifest.arms[partner].file) if need_partner else []

    # When resampling, drive both twin arms to a COMMON per-draw token budget
    # (fraction of the smaller pool) instead of a fraction of each arm's own mass.
    # The full-pool grounded/language ratio can sit right at the twin tolerance,
    # where per-document granularity tips an independent draw over it; a common
    # budget keeps every draw matched with margin.
    common_target = sample_fraction * min(_token_count(raw), _token_count(partner_raw)) if (resampling and need_partner) else None

    docs = subsample_documents(raw, arm=arm, fraction=sample_fraction, sample_seed=sample_seed, target_tokens=common_target)
    _validate_arm(arm, spec, docs, decontaminate=decontaminate, max_jaccard=max_jaccard)

    if check_twin and is_twin:
        partner_docs = subsample_documents(
            partner_raw, arm=partner, fraction=sample_fraction, sample_seed=sample_seed, target_tokens=common_target
        )
        _validate_arm(
            partner,
            manifest.arms[partner],
            partner_docs,
            decontaminate=decontaminate,
            max_jaccard=max_jaccard,
        )
        g, lm = (docs, partner_docs) if arm == "grounded" else (partner_docs, docs)
        validate_twin(manifest, g, lm)

    return docs
