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
import glob
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# CODE — a hit here is decisive. The study is cited by the model or its suite,
# so it was available during development and cannot test the model built to
# match it.
CODE_DIRS = ("model", "tests", "tools")

# THE LEDGER — a hit here is a WARNING, not a verdict, and this distinction was
# the whole point of adding the search.
#
# `reference_values.md` holds 63 PMIDs with their tables TRANSCRIBED. Many of
# those informed a parameter without any test ever citing the identifier, so a
# code-only search returns "NOT FOUND, safe to register" for a study whose
# numbers are sitting in the ledger and were used for calibration. That is
# exactly the silent, self-serving failure this tool exists to prevent: forget
# the paper, register it as unseen, predict well because the model was shaped by
# it, report a success.
#
# But a hard fail here would over-exclude in the other direction. The backlog
# lists papers as FUTURE candidates — mentioned, never read for values, and
# never used. Ruling those out would discard legitimate targets for no reason.
#
# So: print the evidence and let a human judge, with the two kinds of document
# weighted differently.
LEDGER_FILES = ("docs/reference_values.md", "docs/validation_log.md")
MENTION_GLOBS = ("docs/*.md", "preregistration/*.md")


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

    def scan(p):
        out = []
        try:
            for i, line in enumerate(
                    open(p, encoding="utf-8", errors="replace"), start=1):
                if needle in line.lower():
                    out.append((os.path.relpath(p, ROOT), i, line.strip()))
        except OSError:
            pass
        return out

    code_hits = []
    for d in CODE_DIRS:
        base = os.path.join(ROOT, d)
        for dirpath, _dirs, files in os.walk(base) if os.path.isdir(base) else ():
            if "__pycache__" in dirpath:
                continue
            for fn in files:
                if fn.endswith(".py"):
                    code_hits += scan(os.path.join(dirpath, fn))

    ledger_hits, mention_hits = [], []
    for rel in LEDGER_FILES:
        ledger_hits += scan(os.path.join(ROOT, rel))
    ledger_names = set(LEDGER_FILES)
    for pattern in MENTION_GLOBS:
        for p in sorted(glob.glob(os.path.join(ROOT, pattern))):
            if os.path.relpath(p, ROOT) not in ledger_names:
                mention_hits += scan(p)

    def show(hits, limit=8):
        for path, ln, text in hits[:limit]:
            print(f"  {path}:{ln}")
            print(f"      {text[:150]}")
        if len(hits) > limit:
            print(f"  … and {len(hits) - limit} more")

    print(f"{kind} {needle}\n")

    if code_hits:
        print(f"IN-SAMPLE — {len(code_hits)} occurrence(s) in code.\n")
        show(code_hits, 12)
        print("\nEXCLUDE IT. Record it in preregistration/EXCLUDED.md as IN-SAMPLE.")
        print("A study used during development cannot test the model that was "
              "built to match it, however good a test it would otherwise be.")
        return 1

    print("Not cited in model/, tests/ or tools/.")

    if ledger_hits:
        print(f"\n*** WARNING — {len(ledger_hits)} occurrence(s) IN THE LEDGER. "
              f"READ THESE BEFORE REGISTERING. ***\n")
        show(ledger_hits)
        print("\nThe ledger records papers that were READ, and often their "
              "tables transcribed. If any of those numbers informed a parameter, "
              "this study is IN-SAMPLE even though no test cites it — and a "
              "code-only search would have called it safe.")
        print("Judge it on the lines above: a transcribed table used for "
              "calibration means EXCLUDE; a bare 'candidate, not yet read' "
              "mention does not.")

    if mention_hits:
        print(f"\nNoted — {len(mention_hits)} mention(s) in other working "
              f"documents (backlog, notes, registrations):\n")
        show(mention_hits, 5)
        print("\nA mention as a future candidate does not make a study "
              "in-sample. Listing a paper is not reading it.")

    if not ledger_hits and not mention_hits:
        print("\nNot mentioned anywhere in docs/ or preregistration/ either.")

    print("\nVERDICT: no code citation found. "
          + ("CHECK THE LEDGER HITS ABOVE before registering."
             if ledger_hits else "Safe to register as OUT-OF-SAMPLE."))
    print("Caveat: this matches identifiers, not author names. If the study "
          "could have been used under a bare author-year citation, check by "
          "hand before registering.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
