"""Classify every comment PARAGRAPH as CONTRACT or HISTORY, to see what could move.

WHY. `model/` is 54 % comment (measured 2026-09-28). That is not a defect on its
own — inline comments have repeatedly caught errors AT THE POINT OF DECISION,
which a lookup reference cannot do, because a reference tells you something
exists without telling you it matters. But two different things have merged:

  CONTRACT  what you must not do, which convention this is, what the units are,
            where the number came from. **Belongs inline, at the definition.**
  HISTORY   what was tried, what was wrong, when, and what it cost.
            **Belongs in docs/validation_log.md**, with a dated pointer.

THE UNIT IS THE PARAGRAPH, AND THAT CORRECTION IS THE WHOLE POINT. A first
version classified per LINE and put 74 % of lines in "neutral" — because a
history paragraph carries its date on ONE line and three unmarked continuations,
so the continuations scored nothing and no contiguous run ever reached four
lines. **It was measuring sentence wrapping, not content.** A paragraph is also
the unit you would actually move.

HEURISTIC, AND IT WILL BE WRONG SOMETIMES. It writes every classified paragraph
to a report so a sample can be checked against the source. `state_dump.py` cried
wolf three times on its first run and `consistency_audit.py` twice; assume this
one does too. **Do not act on the totals without reading the report.**

    python tools/comment_audit.py [--report PATH]
"""

import argparse
import pathlib
import re

TRIPLE_D = '"' * 3
TRIPLE_S = "'" * 3

# HISTORY: something that HAPPENED — dates, commits, past tense, defect narrative.
HISTORY = [
    (r"\b20\d\d-\d\d-\d\d\b", "date"),
    (r"\b(until|since) 20\d\d", "since/until"),
    (r"\b(was|were|had been|used to|turned out|previously|originally|formerly)\b", "past tense"),
    (r"\b(silently|for months|blew up|crept back|cost (us |real )?(time|days))\b", "defect narrative"),
    (r"\b(this file said|an earlier version|the entry said|it had not|I claimed)\b", "self-correction"),
    (r"\b(found|discovered|caught|noticed) (by|while|on|in)\b", "discovery"),
]
# CONTRACT: a rule, a convention, a unit, a provenance.
CONTRACT = [
    (r"\b(do not|don't|never|must|shall|always)\b", "prohibition"),
    (r"\b(transmural|intraluminal|central aortic|brachial|end-diastolic|cycle mean)\b", "convention"),
    (r"(mmHg|mL/mmHg|L/min|mcg/kg/min|cmH2O|bpm)", "units"),
    (r"1\.0 = |= no effect|\bidentity\b|bit-for-bit", "identity rule"),
    (r"\b(PMID|DOI|PMC)\b", "provenance"),
]


def marks(text):
    h = {w for p, w in HISTORY if re.search(p, text, re.I)}
    c = {w for p, w in CONTRACT if re.search(p, text, re.I)}
    return h, c


def blocks_of(path):
    """Yield (start, end, [lines]) for each comment paragraph, layout dropped."""
    noise = re.compile(r"^(-{3,}|={3,}|_{3,})$")
    cur, out = [], []
    in_doc, q = False, None
    for i, ln in enumerate(path.read_text().splitlines(), 1):
        t = ln.strip()
        is_comment = False
        if in_doc:
            is_comment = True
            if q in t:
                in_doc = False
        elif t.startswith(TRIPLE_D) or t.startswith(TRIPLE_S):
            q = t[:3]
            is_comment = True
            if not (len(t) > 3 and t.endswith(q)):
                in_doc = True
        elif t.startswith("#"):
            is_comment = True
        body = t.lstrip("#").strip().strip(TRIPLE_D).strip(TRIPLE_S).strip()
        if is_comment and body and not noise.match(body):
            cur.append((i, ln))
        else:
            if cur:
                out.append((cur[0][0], cur[-1][0], [x[1] for x in cur]))
                cur = []
    if cur:
        out.append((cur[0][0], cur[-1][0], [x[1] for x in cur]))
    return out


def classify_block(lines):
    h, c = marks(" ".join(lines))
    if h and c:
        return "mixed", ",".join(sorted(h | c))
    if h:
        return "history", ",".join(sorted(h))
    if c:
        return "contract", ",".join(sorted(c))
    return "neutral", ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--report", default="comment_audit_report.txt")
    args = ap.parse_args()

    root = pathlib.Path(__file__).resolve().parent.parent
    totals = {"contract": 0, "history": 0, "mixed": 0, "neutral": 0}
    per_file, big = [], []

    with open(args.report, "w") as rep:
        for f in sorted((root / "model").glob("*.py")):
            counts = dict.fromkeys(totals, 0)
            for a, b, lines in blocks_of(f):
                kind, why = classify_block(lines)
                n = len(lines)
                counts[kind] += n
                totals[kind] += n
                rep.write("\n=== %s:%d-%d  %s (%d lines)  [%s]\n"
                          % (f.name, a, b, kind.upper(), n, why))
                for ln in lines:
                    rep.write("    " + ln + "\n")
                if kind in ("history", "mixed") and n >= 5:
                    head = lines[0].strip().lstrip("#").strip()[:60]
                    big.append((f.name, a, b, n, kind, head))
            per_file.append((f.name, counts))

    print("%-22s %9s %8s %6s %8s" % ("file", "contract", "history", "mixed", "neutral"))
    for name, c in sorted(per_file, key=lambda r: -(r[1]["history"] + r[1]["mixed"])):
        if sum(c.values()):
            print("%-22s %9d %8d %6d %8d"
                  % (name, c["contract"], c["history"], c["mixed"], c["neutral"]))
    n = sum(totals.values()) or 1
    print("%-22s %9d %8d %6d %8d   (%d comment lines, layout excluded)"
          % ("TOTAL", totals["contract"], totals["history"], totals["mixed"],
             totals["neutral"], n))
    print()
    print("PURE HISTORY : %5d lines (%2.0f %%) -- movable to the log with a dated pointer"
          % (totals["history"], 100 * totals["history"] / n))
    print("MIXED        : %5d lines (%2.0f %%) -- rule and story woven together; REWRITE, not cut"
          % (totals["mixed"], 100 * totals["mixed"] / n))
    print("CONTRACT     : %5d lines (%2.0f %%) -- stays where it is"
          % (totals["contract"], 100 * totals["contract"] / n))
    print("NEUTRAL      : %5d lines (%2.0f %%) -- explains the mechanism; judgement call"
          % (totals["neutral"], 100 * totals["neutral"] / n))
    print()
    print("LARGEST HISTORY / MIXED PARAGRAPHS (5+ lines): %d paragraphs, %d lines"
          % (len(big), sum(x[3] for x in big)))
    for name, a, b, ln, kind, head in sorted(big, key=lambda r: -r[3])[:12]:
        print("  %-18s %4d-%-4d %3d  %-8s %s" % (name, a, b, ln, kind, head))
    print()
    print("Per-paragraph detail in " + args.report)
    print("SAMPLE IT BEFORE ACTING. Heuristic, and no test asserts it.")


if __name__ == "__main__":
    main()
