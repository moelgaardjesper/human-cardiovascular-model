#!/usr/bin/env python3
"""Is this study already in the model? Run before registering a prediction.

    python3 tools/check_insample.py 31560715
    python3 tools/check_insample.py 10.1097/ALN.0b013e3181672607
    python3 tools/check_insample.py PMC6764667

Exit 0 = NOT FOUND, safe to register as out-of-sample.
Exit 1 = FOUND, the study is in-sample and must be excluded.

WHY THIS IS A TOOL AND NOT A JUDGEMENT CALL.

A blind validation is worthless if the "unseen" study turns out to have been
used during development. The obvious safeguard — remembering which papers were
used — is exactly the safeguard that fails, because 62 sources is well past what
anyone recalls reliably, and the failure is silent and self-serving: you forget
the paper you used, register it as out-of-sample, predict well because the model
was built to match it, and report a success.

Likhvantsev 2025 is the known case. It was used from the very beginning, and
that is why it cannot appear in the blind phase no matter how good a test the
tilt meta-analysis would otherwise make.

This searches model/ and tests/ for the identifier — the same files the source
index is derived from. It matches PMIDs, PMCIDs and DOIs, case-insensitively,
and reports every line it found so the caller can see the context rather than
trusting a yes/no.

IT MATCHES IDENTIFIERS, NOT NAMES. A study cited in the code by author and year
alone would not be caught. That gap was closed on 2026-09-16 — every author-year
citation in the repository now carries a PMID, PMC or DOI — but if a bare
author-year citation is ever reintroduced, this check goes blind to it. Run
`tools/source_index.py --unasserted` occasionally to confirm that has not
happened.
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEARCH_DIRS = ("model", "tests", "tools")


def normalise(raw):
    """Return (kind, needle) for a PMID, PMCID or DOI."""
    s = raw.strip().rstrip(".,;")
    s = re.sub(r"^https?://(dx\.)?doi\.org/", "", s, flags=re.I)
    s = re.sub(r"^https?://(www\.)?ncbi\.nlm\.nih\.gov/pmc/articles/", "", s, flags=re.I)
    s = re.sub(r"^https?://pubmed\.ncbi\.nlm\.nih\.gov/", "", s, flags=re.I).strip("/")
    if re.fullmatch(r"PMC\d{6,8}", s, flags=re.I):
        return "PMCID", s.upper()
    if re.fullmatch(r"\d{7,8}", s):
        return "PMID", s
    if s.lower().startswith("10."):
        return "DOI", s.lower()
    return "UNKNOWN", s.lower()


def main(argv):
    if len(argv) != 2:
        print(__doc__.strip().split("\n\n")[1], file=sys.stderr)
        return 2
    kind, needle = normalise(argv[1])
    if kind == "UNKNOWN":
        print(f"Cannot tell what kind of identifier {argv[1]!r} is. "
              f"Give a PMID, a PMCID or a DOI.", file=sys.stderr)
        return 2

    hits = []
    for d in SEARCH_DIRS:
        base = os.path.join(ROOT, d)
        if not os.path.isdir(base):
            continue
        for dirpath, _dirs, files in os.walk(base):
            if "__pycache__" in dirpath:
                continue
            for fn in files:
                if not fn.endswith(".py"):
                    continue
                p = os.path.join(dirpath, fn)
                for i, line in enumerate(
                        open(p, encoding="utf-8", errors="replace"), start=1):
                    if needle in line.lower():
                        hits.append((os.path.relpath(p, ROOT), i, line.strip()))

    print(f"{kind} {needle}\n")
    if not hits:
        print("NOT FOUND in model/, tests/ or tools/.")
        print("\nSafe to register as OUT-OF-SAMPLE.")
        print("Caveat: this matches identifiers, not author names. If the study "
              "could have been used under a bare author-year citation, check by "
              "hand before registering.")
        return 0

    print(f"FOUND — {len(hits)} occurrence(s). THIS STUDY IS IN-SAMPLE.\n")
    for path, ln, text in hits[:12]:
        print(f"  {path}:{ln}")
        print(f"      {text[:150]}")
    if len(hits) > 12:
        print(f"  … and {len(hits) - 12} more")
    print("\nEXCLUDE IT. Record it in preregistration/EXCLUDED.md as IN-SAMPLE.")
    print("A study used during development cannot test the model that was built "
          "to match it, however good a test it would otherwise be.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
