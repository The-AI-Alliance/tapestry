#!/usr/bin/env python3
"""Assemble an EXP-001 corpus from permissively-licensed sources.

Implements the matched-twin design from ``data/README.md``: both the
**grounded** and **language-matched** arms are drawn from the *same source and
register* (Wikipedia article intros, CC-BY-SA-4.0), varying only the topical
**domain** — value-laden domains (law, religion, family, civic) for grounded,
value-neutral domains (weather, sports, technical, mathematics) for the twin.
That holds language, register, recency and quality constant by construction, so
the only systematic difference is cultural value content.

The fetcher then does what a hand-assembled corpus would otherwise get wrong:
  * drops any document that trips WVS decontamination (so it never reaches CPT);
  * balances the two arms' token budgets to within the twin tolerance;
  * writes a manifest declaring the controls, and re-validates the result.

Default run fetches an English **demonstration seed** (real text, verifiable
titles) — it exercises the loader end to end. ``usa``/English is deliberately a
*wiring* culture, not the experimental one (the spec wants a high-WVS-distance
culture); supply ``--titles-file`` + ``--lang`` to assemble a real target
culture in its own language.

Examples::

    # real English demonstration seed -> data/seed-example/
    python fetch_corpus.py --culture seed-example --lang en --per-domain 4

    # a real target culture from a curated title list in its language
    python fetch_corpus.py --culture egypt --lang ar --titles-file egypt_titles.json

    # validate an existing root against every control, no fetching
    python fetch_corpus.py --validate data/seed-example
"""

# pylint: disable=wrong-import-position

from __future__ import annotations

import argparse
import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from cultural_cpt import dataset  # noqa: E402

# Same source + register for both arms; only the domain (value-laden vs neutral)
# differs. Titles are real, stable English Wikipedia articles, used for the
# demonstration seed. Real target cultures pass their own --titles-file.
_DEFAULT_TITLES: dict[str, dict[str, list[str]]] = {
    "grounded": {
        "law": ["Law", "Constitution", "Justice", "Rule of law", "Common law"],
        "religion": ["Religion", "Ethics", "Morality", "Ritual", "Pilgrimage"],
        "family": ["Family", "Kinship", "Marriage", "Filial piety", "Extended family"],
        "civic": ["Citizenship", "Democracy", "Civil society", "Tradition", "Social contract"],
    },
    "language_matched": {
        "weather": ["Weather", "Rain", "Cloud", "Wind", "Atmospheric pressure"],
        "sports": ["Association football", "Basketball", "Tennis", "Olympic Games", "Marathon"],
        "technical": ["Internal combustion engine", "Screw", "Concrete", "Bridge", "Bearing (mechanical)"],
        "mathematics": ["Prime number", "Triangle", "Calculus", "Logarithm", "Matrix (mathematics)"],
    },
}

_WIKI_LICENSE = "CC-BY-SA-4.0"
_USER_AGENT = "tapestry-cultural-cpt/0.1 (EXP-001 corpus fetcher; +https://thealliance.ai)"
_INTRO_CAP = 120  # words per doc in seed/intro mode (small, comparable)
_FULL_CAP = 2000  # words per doc in --full mode (real-sized CPT corpus)


def _wiki_text(lang: str, title: str, *, full: bool) -> tuple[str, str] | None:
    """Fetch an article's plain text. ``full`` grabs the whole article, else just
    the lead section. Returns (text, canonical_url) or None if missing."""
    params = {
        "action": "query",
        "format": "json",
        "prop": "extracts",
        "explaintext": "1",
        "redirects": "1",
        "titles": title,
    }
    if not full:
        params["exintro"] = "1"
    url = f"https://{lang}.wikipedia.org/w/api.php?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as resp:  # noqa: S310 (trusted host)
        data = json.loads(resp.read().decode("utf-8"))
    pages = data.get("query", {}).get("pages", {})
    for page in pages.values():
        extract = (page.get("extract") or "").strip()
        if not extract or "missing" in page:
            return None
        canonical = page.get("title", title)
        page_url = f"https://{lang}.wikipedia.org/wiki/" + urllib.parse.quote(canonical.replace(" ", "_"))
        return extract, page_url
    return None


def _truncate_words(text: str, max_words: int) -> str:
    words = text.split()
    return text if len(words) <= max_words else " ".join(words[:max_words])


def _category_members(lang: str, category: str, limit: int) -> list[str]:
    """Article titles in a Wikipedia category (pages only), via the action API.

    Used to scale a domain past hand-curated titles. Categories are chosen narrow
    (e.g. fiqh, ethics, worship) so the value-laden vs neutral contrast survives;
    off-topic members are diluted by the law of large numbers + decontamination.
    """
    params = {
        "action": "query",
        "format": "json",
        "list": "categorymembers",
        "cmtitle": category,
        "cmlimit": str(min(limit, 500)),
        "cmtype": "page",
    }
    url = f"https://{lang}.wikipedia.org/w/api.php?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:  # noqa: S310
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as exc:
        print(f"  ! category {category}: {exc}", file=sys.stderr)
        return []
    members = data.get("query", {}).get("categorymembers", [])
    return [m["title"] for m in members][:limit]


def _fetch_arm(
    lang: str,
    domains: dict[str, list[str]],
    per_domain: int,
    *,
    full: bool,
    max_words: int = 0,
    categories: dict[str, list[str]] | None = None,
    cat_limit: int = 0,
) -> list[dict]:
    cap = (max_words or _FULL_CAP) if full else _INTRO_CAP
    docs: list[dict] = []
    for domain, titles in domains.items():
        # Candidate titles: curated, then category members (deduped, order kept).
        candidates = list(titles)
        if cat_limit and categories:
            for cat in categories.get(domain, []):
                candidates += _category_members(lang, cat, cat_limit)
        seen: set[str] = set()
        candidates = [t for t in candidates if not (t in seen or seen.add(t))]
        budget = per_domain if not (cat_limit and categories) else len(candidates)
        taken = 0
        for title in candidates:
            if taken >= budget:
                break
            try:
                got = _wiki_text(lang, title, full=full)
            except Exception as exc:  # network / API hiccup: skip, keep going
                print(f"  ! {lang}:{title}: {exc}", file=sys.stderr)
                continue
            if not got:
                print(f"  - {lang}:{title}: no extract, skipping", file=sys.stderr)
                continue
            text, page_url = got
            text = _truncate_words(text, cap)
            if len(text.split()) < 20:  # too short to be useful CPT text
                continue
            slug = title.lower().replace(" ", "_").replace("(", "").replace(")", "")
            docs.append(
                {
                    "id": f"{lang}wiki:{domain}:{slug}",
                    "text": text,
                    "source": f"{lang}.wikipedia.org",
                    "license": _WIKI_LICENSE,
                    "lang": lang,
                    "domain": domain,
                    "url": page_url,
                }
            )
            taken += 1
            print(f"  + {domain:<12} {title} ({len(text.split())} words)")
    return docs


def _decontaminate(docs: list[dict], arm: str) -> list[dict]:
    """Drop any fetched doc that reproduces a WVS/behavioral item."""
    records = [dataset.DocumentRecord.from_json(d, where=f"{arm}:fetch") for d in docs]
    flags = {f.doc_id for f in dataset.find_contamination(records, dataset.wvs_probe_phrases())}
    if flags:
        print(f"  decontamination dropped {len(flags)} doc(s) from {arm}: {sorted(flags)}", file=sys.stderr)
    return [d for d in docs if d["id"] not in flags]


def _balance_twin(grounded: list[dict], matched: list[dict], tol: float) -> None:
    """Trim the longer arm's documents (in place) until token budgets match.

    Keeps both arms real text — it only shortens documents to equalize size, the
    twin control the spec demands ("size held constant").
    """

    def total(docs: list[dict]) -> int:
        return sum(len(dataset._normalize(d["text"])) for d in docs)

    for _ in range(1000):
        g, m = total(grounded), total(matched)
        if m == 0 or abs(1.0 - g / m) <= tol:
            return
        longer = grounded if g > m else matched
        longest = max(longer, key=lambda d: len(d["text"].split()))
        words = longest["text"].split()
        if len(words) <= 20:
            return  # cannot trim further without going below the usefulness floor
        longest["text"] = " ".join(words[: int(len(words) * 0.9)])


def _cap_tokens(docs: list[dict], max_tokens: int, *, seed: int = 0) -> list[dict]:
    """Subsample an arm's docs to a token budget (deterministic), so corpus size
    -- and therefore training time -- is predictable regardless of how many
    category members were pulled. Shuffled first so the cap keeps a domain mix."""
    if not max_tokens:
        return docs
    import random as _random

    shuffled = docs[:]
    _random.Random(seed).shuffle(shuffled)
    out: list[dict] = []
    total = 0
    for d in shuffled:
        n = len(dataset._normalize(d["text"]))
        if total + n > max_tokens and out:
            break
        out.append(d)
        total += n
    return out


def _write_jsonl(path: Path, docs: list[dict]) -> None:
    path.write_text("".join(json.dumps(d, ensure_ascii=False) + "\n" for d in docs), encoding="utf-8")


def _write_manifest(root: Path, culture: str, lang: str, tol: float, titles: dict) -> None:
    def arm(name: str, value_laden: bool) -> dict:
        return {
            "file": f"{name}.jsonl",
            "lang": lang,
            "register": "encyclopedic",
            "domains": sorted(titles[name].keys()),
            "value_laden": value_laden,
        }

    manifest = {
        "culture": culture,
        "language": lang,
        "arms": {
            "grounded": arm("grounded", True),
            "language_matched": arm("language_matched", False),
        },
        "twin_matching": {
            "token_ratio_tolerance": tol,
            "require_same_language": True,
            "require_same_register": True,
        },
    }
    (root / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _validate(root: Path) -> int:
    manifest = dataset.CorpusManifest.load(root)
    print(f"validating {root}  (culture={manifest.culture}, lang={manifest.language})")
    for arm in manifest.arms:
        docs = dataset.load_arm_documents(root, arm)
        tokens = sum(len(dataset._normalize(d.text)) for d in docs)
        print(f"  {arm:<20} {len(docs):>4} docs  {tokens:>7} tokens  OK")
    print("all controls passed (license, language, register, token budget, recency, decontamination)")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--culture", default="seed-example", help="corpus / culture name")
    parser.add_argument("--lang", default="en", help="Wikipedia language code (e.g. en, ar, vi)")
    parser.add_argument("--per-domain", type=int, default=4, help="articles per domain per arm")
    parser.add_argument(
        "--full",
        action="store_true",
        help=f"fetch full articles (cap {_FULL_CAP} words) for a real-sized corpus, not just intros",
    )
    parser.add_argument(
        "--max-words",
        type=int,
        default=0,
        help=f"override the per-article word cap in --full mode (default {_FULL_CAP})",
    )
    parser.add_argument("--titles-file", default="", help="JSON {arm: {domain: [titles]}} for a real culture")
    parser.add_argument(
        "--cat-limit",
        type=int,
        default=0,
        help="also pull up to N article(s) per category from the titles file's 'categories' block (0 = off)",
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=0,
        help="per-arm token budget; subsample to this so corpus size / training time is predictable (0 = no cap)",
    )
    parser.add_argument("--tol", type=float, default=0.20, help="twin token-ratio tolerance")
    parser.add_argument("--out", default="", help="output root (default: data/<culture>)")
    parser.add_argument("--validate", default="", help="validate an existing root and exit")
    args = parser.parse_args()

    if args.validate:
        return _validate(Path(args.validate))

    titles = _DEFAULT_TITLES
    if args.titles_file:
        titles = json.loads(Path(args.titles_file).read_text(encoding="utf-8"))
    elif args.lang != "en":
        print("error: non-English fetch needs --titles-file with target-language titles", file=sys.stderr)
        return 2

    root = Path(args.out) if args.out else Path(__file__).resolve().parent / "data" / args.culture
    root.mkdir(parents=True, exist_ok=True)

    cats = titles.get("categories", {}) if isinstance(titles, dict) else {}
    print(f"fetching grounded arm ({args.lang}{', full' if args.full else ''})…")
    grounded = _decontaminate(
        _fetch_arm(
            args.lang,
            titles["grounded"],
            args.per_domain,
            full=args.full,
            max_words=args.max_words,
            categories=cats.get("grounded"),
            cat_limit=args.cat_limit,
        ),
        "grounded",
    )
    print(f"fetching language_matched arm ({args.lang}{', full' if args.full else ''})…")
    matched = _decontaminate(
        _fetch_arm(
            args.lang,
            titles["language_matched"],
            args.per_domain,
            full=args.full,
            max_words=args.max_words,
            categories=cats.get("language_matched"),
            cat_limit=args.cat_limit,
        ),
        "language_matched",
    )
    if not grounded or not matched:
        print("error: one or both arms came back empty (network? titles?)", file=sys.stderr)
        return 1

    grounded = _cap_tokens(grounded, args.max_tokens)
    matched = _cap_tokens(matched, args.max_tokens)
    _balance_twin(grounded, matched, args.tol)
    _write_jsonl(root / "grounded.jsonl", grounded)
    _write_jsonl(root / "language_matched.jsonl", matched)
    _write_manifest(root, args.culture, args.lang, args.tol, titles)
    print(f"wrote {root}")
    return _validate(root)


if __name__ == "__main__":
    raise SystemExit(main())
