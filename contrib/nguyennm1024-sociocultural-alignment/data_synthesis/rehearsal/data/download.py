"""Idempotent HuggingFace download driver.

Iterates SOURCES + DECONTAM_TESTSETS and calls `datasets.load_dataset` for
each, triggering the HF cache to populate. Already-cached entries are
detected and skipped by `datasets` itself; this script just reports what
happened.

Failures (404, auth-required, network) are caught per-source so a single bad
dataset doesn't block the rest. The exit code is non-zero if any source
failed, so it's safe to wire into CI.

Run via `python -m rehearsal.cli download` (preferred) or directly:
    python -m rehearsal.data.download --test-only
"""
from __future__ import annotations

import argparse
import sys
import time
from dataclasses import dataclass
from typing import Any, Iterable

from .sources import (
    DECONTAM_TESTSETS,
    DecontamTestset,
    HFSource,
    SOURCES,
)


@dataclass
class DownloadResult:
    name: str
    hf_path: str
    status: str            # "ok" | "skipped" | "failed" | "no_hf_path"
    rows: int | None = None
    elapsed_s: float | None = None
    error: str | None = None


def _try_load(
    hf_path: str,
    hf_config: str | None,
    hf_split: str,
    *,
    trust_remote_code: bool,
) -> tuple[int, str | None]:
    """Returns (row_count, error). Uses `datasets.load_dataset`."""
    try:
        from datasets import load_dataset  # local import — keeps cli import cheap
    except ImportError:
        return -1, "datasets library not installed (pip install datasets)"

    try:
        kwargs: dict[str, Any] = {"split": hf_split}
        if hf_config:
            kwargs["name"] = hf_config
        if trust_remote_code:
            kwargs["trust_remote_code"] = True
        ds = load_dataset(hf_path, **kwargs)
        return len(ds), None
    except Exception as e:
        return -1, repr(e)


def _download_one(
    name: str,
    hf_path: str | None,
    hf_config: str | None,
    hf_split: str,
) -> DownloadResult:
    if hf_path is None:
        return DownloadResult(name=name, hf_path="<none>", status="no_hf_path")
    t0 = time.time()
    # First attempt without trust_remote_code; some legacy datasets demand it.
    rows, err = _try_load(hf_path, hf_config, hf_split, trust_remote_code=False)
    if err and "trust_remote_code" in err:
        rows, err = _try_load(hf_path, hf_config, hf_split, trust_remote_code=True)
    elapsed = time.time() - t0
    if err:
        return DownloadResult(
            name=name, hf_path=hf_path, status="failed",
            elapsed_s=elapsed, error=err,
        )
    return DownloadResult(
        name=name, hf_path=hf_path, status="ok",
        rows=rows, elapsed_s=elapsed,
    )


def _filter_train_sources(
    sources: list[HFSource],
    source_filter: str | None,
) -> list[HFSource]:
    """Drop generated/programmatic sources (nothing to download). Apply name filter."""
    out = [s for s in sources if s.hf_path is not None]
    if source_filter:
        out = [s for s in out if s.name == source_filter]
    return out


def _filter_decontam_testsets(
    testsets: list[DecontamTestset],
    source_filter: str | None,
) -> list[DecontamTestset]:
    if source_filter:
        return [t for t in testsets if t.name == source_filter]
    return list(testsets)


def run_download(
    *,
    train_only: bool = False,
    test_only: bool = False,
    source_filter: str | None = None,
    log=sys.stderr,
) -> list[DownloadResult]:
    """Drive the downloads. Returns list of per-source results."""
    if train_only and test_only:
        raise ValueError("--train-only and --test-only are mutually exclusive")

    results: list[DownloadResult] = []

    if not test_only:
        train_targets = _filter_train_sources(SOURCES, source_filter)
        print(f"[download] {len(train_targets)} training sources to fetch", file=log)
        for i, src in enumerate(train_targets, 1):
            print(
                f"[download] ({i}/{len(train_targets)}) train: {src.name} -> {src.hf_path}"
                + (f" [{src.hf_config}]" if src.hf_config else "")
                + f" [{src.hf_split}]",
                file=log, flush=True,
            )
            r = _download_one(src.name, src.hf_path, src.hf_config, src.hf_split)
            results.append(r)
            _print_result(r, log)

    if not train_only:
        decontam_targets = _filter_decontam_testsets(DECONTAM_TESTSETS, source_filter)
        print(f"[download] {len(decontam_targets)} decontam test sets to fetch", file=log)
        for i, ts in enumerate(decontam_targets, 1):
            print(
                f"[download] ({i}/{len(decontam_targets)}) decontam: {ts.name} -> {ts.hf_path}"
                + (f" [{ts.hf_config}]" if ts.hf_config else "")
                + f" [{ts.hf_split}]",
                file=log, flush=True,
            )
            r = _download_one(ts.name, ts.hf_path, ts.hf_config, ts.hf_split)
            results.append(r)
            _print_result(r, log)

    _summary(results, log)
    return results


def _print_result(r: DownloadResult, log) -> None:
    if r.status == "ok":
        print(f"    ok ({r.rows} rows, {r.elapsed_s:.1f}s)", file=log, flush=True)
    elif r.status == "no_hf_path":
        print(f"    skipped (generated/programmatic source, no HF path)", file=log, flush=True)
    elif r.status == "failed":
        print(f"    FAILED: {r.error}", file=log, flush=True)


def _summary(results: Iterable[DownloadResult], log) -> None:
    by_status: dict[str, int] = {}
    failed: list[DownloadResult] = []
    for r in results:
        by_status[r.status] = by_status.get(r.status, 0) + 1
        if r.status == "failed":
            failed.append(r)
    print("", file=log)
    print(f"[download] summary: {by_status}", file=log)
    if failed:
        print(f"[download] {len(failed)} failed:", file=log)
        for r in failed:
            print(f"    - {r.name} ({r.hf_path}): {r.error}", file=log)


def main() -> int:
    p = argparse.ArgumentParser(description="Download HF datasets into the local cache.")
    p.add_argument("--train-only", action="store_true",
                   help="Skip decontam test sets.")
    p.add_argument("--test-only", action="store_true",
                   help="Skip training sources.")
    p.add_argument("--source", default=None,
                   help="Restrict to one named source (training OR decontam).")
    args = p.parse_args()

    results = run_download(
        train_only=args.train_only,
        test_only=args.test_only,
        source_filter=args.source,
    )
    any_failed = any(r.status == "failed" for r in results)
    return 1 if any_failed else 0


if __name__ == "__main__":
    sys.exit(main())
