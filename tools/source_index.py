#!/usr/bin/env python3
"""
Every source the model cites, and the test that asserts it — DERIVED, not typed.

    python3 tools/source_index.py               # human-readable
    python3 tools/source_index.py --markdown    # for the freeze artefact
    python3 tools/source_index.py --unasserted  # only the risky quadrant

WHY THIS EXISTS, AND WHY IT IS GENERATED.

The curated validation table in `tools/validation_table.py` is REPRESENTATIVE —
about a dozen headline comparisons, kept short enough that a person will read
it. It is not the evidence base, and it went stale: two of its rows compared the
model against protocols it was not being run at, and nothing caught it, because
a reporting tool has no test watching it.

The obvious fix — a bigger hand-written table listing every paper — fails the
same way, only faster. A list that must be kept in step with 84 test functions
by hand WILL drift. So the complete record is DERIVED from the code that already
carries it: every test docstring and every section header already names its
source with a PMID or DOI, and the ratchet keeps those honest for free.

WHAT IT REPORTS, one row per SOURCE:
  - the identifiers (PMID and DOI merged when they name the same paper)
  - the citation context, as written in the code
  - which tests assert it, and whether those are strict xfails
  - whether it is cited in `model/` — a parameter justification

THE RISKY QUADRANT IS THE POINT. A source cited in `model/` whose identifier no
test repeats is a paper justifying a parameter with nothing checking it — the
citation form of "documented mechanism, silently inert", which is this
repository's most frequent defect class. `--unasserted` lists exactly those.

IT MATCHES IDENTIFIERS, NOT NAMES, and that boundary must be read literally. A
test naming a paper in prose without its PMID is invisible here, so that source
appears untested. One such case is known. The `--unasserted` list is therefore
an UPPER BOUND, and a source on it means either "write the test" or "put the
identifier into the test that already exists".

WHAT IT CANNOT SEE. Papers read and set aside without producing a test exist
only in `docs/reference_values.md`, which is the project's lab notebook and is
not published. Those belong in a short hand-written "consulted, not asserted"
list in the manuscript — a gap this tool states rather than hides.
"""
import argparse
import ast
import os
import re
import sys
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PMID_RE = re.compile(r"PMID:?\s*([0-9]{7,8})", re.I)
# PMC is a THIRD identifier namespace and was missed on the first pass: 13 of
# them appear in tests/ and model/, and a source cited only by PMC was invisible
# to this tool — neither indexed nor reported as unasserted, simply absent.
PMC_RE = re.compile(r"\b(PMC[0-9]{6,8})\b", re.I)
DOI_RE = re.compile(r"\b(10\.\d{4,5}/[A-Za-z0-9./_():;-]*[A-Za-z0-9)])")
# A section header in the test file: "# ===..." then "# 28. Title — Source".
SECTION_RE = re.compile(r"^#\s*={10,}\s*$")


def _clean(line):
    """Strip comment and docstring furniture from a source line."""
    return line.strip().lstrip("#").strip().strip('"').strip()


def citations_in(text):
    """Every citation token in `text`, as (line_no, kind, identifier)."""
    found = []
    for i, line in enumerate(text.splitlines(), start=1):
        for m in PMID_RE.finditer(line):
            found.append((i, "pmid", m.group(1)))
        for m in PMC_RE.finditer(line):
            found.append((i, "pmc", m.group(1).upper()))
        for m in DOI_RE.finditer(line):
            doi = m.group(1).rstrip(".,;)")
            found.append((i, "doi", doi.lower()))
    return found


def test_spans(path, text):
    """Map every test function to (start, end, markers) using the AST.

    Decorators are read for pytest markers, so a strict xfail is reported as
    one. A source whose only test is an xfail is NOT validated by it — it is
    contradicted by it — and the index must not let those look alike.
    """
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return []
    spans = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef) or not node.name.startswith("test_"):
            continue
        markers = []
        for dec in node.decorator_list:
            src = ast.unparse(dec)
            if "xfail" in src:
                markers.append("XFAIL(strict)" if "strict=True" in src else "xfail")
            for tag in ("slow", "overnight"):
                if f"mark.{tag}" in src:
                    markers.append(tag)
        start = min([node.lineno] + [d.lineno for d in node.decorator_list])
        spans.append((start, node.end_lineno, node.name, markers))
    return sorted(spans)


def citation_blocks(cite_lines, gap=15):
    """Group module-level citation lines into reference BLOCKS.

    A section header in these files reads as a run of comment lines carrying
    several identifiers for one or two papers — "PMID 2916705  DOI 10.1152/..."
    on adjacent lines, sometimes [A1] and [A2] listed together. Treating each
    identifier as its own boundary would make every citation in a block truncate
    the next one's window to nothing.
    """
    blocks = []
    for ln in sorted(set(cite_lines)):
        if blocks and ln - blocks[-1][-1] <= gap:
            blocks[-1].append(ln)
        else:
            blocks.append([ln])
    return blocks


def collect():
    """Build {source_key: record} across tests/ and model/."""
    sources = defaultdict(lambda: {
        "pmids": set(), "pmcs": set(), "dois": set(), "context": None,
        "tests": [], "model_files": set(), "test_files": set(),
    })
    # Merge identifiers that appear within this many lines of each other: a
    # header usually writes "PMID 2916705  DOI 10.1152/..." on adjacent lines.
    MERGE_WINDOW = 2
    alias = {}

    def key_for(ident):
        return alias.get(ident, ident)

    for sub in ("tests", "model"):
        d = os.path.join(ROOT, sub)
        if not os.path.isdir(d):
            continue
        for fn in sorted(os.listdir(d)):
            if not fn.endswith(".py"):
                continue
            path = os.path.join(d, fn)
            text = open(path, encoding="utf-8").read()
            lines = text.splitlines()
            cites = citations_in(text)
            if not cites:
                continue

            # --- merge co-located identifiers into one source --------------
            for i, (ln, kind, ident) in enumerate(cites):
                for ln2, kind2, ident2 in cites[i + 1:]:
                    if ln2 - ln > MERGE_WINDOW:
                        break
                    if kind2 != kind:
                        alias.setdefault(ident2, key_for(ident))

            spans = test_spans(path, text) if sub == "tests" else []
            # Module-level citations (section headers) cover the tests that
            # FOLLOW them, up to the next reference block. Anchoring on the
            # "# ====" rules instead was wrong: those come in PAIRS, so the
            # window closed on the header's own closing rule and captured no
            # tests at all — PMID 16695932 is cited at a header and was
            # reported as having no test.
            span_starts = {s[0] for s in spans}
            module_cites = [ln for ln, _k, _i in cites
                            if not any(s[0] <= ln <= s[1] for s in spans)]
            blocks = citation_blocks(module_cites)
            block_window = {}
            for bi, blk in enumerate(blocks):
                start = blk[-1]
                end = blocks[bi + 1][0] if bi + 1 < len(blocks) else 10 ** 9
                for ln in blk:
                    block_window[ln] = (start, end)

            for ln, kind, ident in cites:
                k = key_for(ident)
                rec = sources[k]
                rec[{"pmid": "pmids", "pmc": "pmcs", "doi": "dois"}[kind]].add(ident)
                if rec["context"] is None:
                    ctx = _clean(lines[ln - 1])
                    if len(ctx) < 40 and ln < len(lines):
                        ctx = (ctx + " " + _clean(lines[ln])).strip()
                    rec["context"] = ctx[:200]

                if sub == "model":
                    rec["model_files"].add(f"{sub}/{fn}")
                    continue
                rec["test_files"].add(f"{sub}/{fn}")

                # Inside a test? attribute to it. Otherwise it is a section
                # header, and it covers the tests down to the next header.
                inside = [s for s in spans if s[0] <= ln <= s[1]]
                if inside:
                    s = inside[0]
                    rec["tests"].append((s[2], tuple(s[3])))
                else:
                    lo, hi = block_window.get(ln, (ln, 10 ** 9))
                    for s in spans:
                        if lo <= s[0] < hi:
                            rec["tests"].append((s[2], tuple(s[3])))

    for rec in sources.values():
        rec["tests"] = sorted(set(rec["tests"]))
    return sources


def render(sources, markdown, only_unasserted):
    rows = []
    for _k, rec in sources.items():
        parts = [" ".join(sorted(f"PMID {p}" for p in rec["pmids"])),
                 " ".join(sorted(rec["pmcs"])),
                 " ".join(sorted(rec["dois"]))]
        label = " ".join(p for p in parts if p) or "(no identifier)"
        asserted = bool(rec["tests"])
        if only_unasserted and (asserted or not rec["model_files"]):
            continue
        rows.append((label, rec, asserted))
    rows.sort(key=lambda r: (not r[1]["model_files"], r[0]))

    n_total = len(sources)
    n_asserted = sum(1 for _l, r, a in
                     [(l, r, bool(r["tests"])) for l, r in
                      ((l, r) for l, r, _a in rows)] if a) if rows else 0
    unasserted_model = [r for r in rows if not r[1]["tests"] and r[1]["model_files"]]

    out = []
    if markdown:
        out.append("# Source index — every citation in the model and its test\n")
        out.append("Generated by `tools/source_index.py`. **Nobody maintains this "
                   "file.** It is derived from the PMIDs and DOIs already written "
                   "into the test docstrings and section headers, so it cannot "
                   "drift out of step with the suite.\n")
        out.append(f"**{n_total} distinct sources.** A source with no test named "
                   "beside it is cited in `model/` as a parameter justification "
                   "with no test repeating its identifier — see the note at the "
                   "end for what that does and does not mean.\n")
        out.append("A test marked **XFAIL(strict)** does not validate its source. "
                   "It records a KNOWN, MEASURED disagreement and fails the day "
                   "the gap closes, so the two must not be read alike.\n")
        out.append("| source | cited as | asserted by | status |")
        out.append("|---|---|---|---|")
        for label, rec, asserted in rows:
            tests = rec["tests"]
            if tests:
                shown = "<br>".join(f"`{n}`" for n, _m in tests[:6])
                if len(tests) > 6:
                    shown += f"<br>… and {len(tests) - 6} more"
                marks = sorted({m for _n, ms in tests for m in ms})
                status = ", ".join(marks) if marks else "pass"
            else:
                shown = "— **no test**"
                status = "parameter justification only"
            where = ", ".join(sorted(rec["model_files"])) or ""
            ctx = (rec["context"] or "").replace("|", "/")
            out.append(f"| {label}{(' <br>*' + where + '*') if where else ''} "
                       f"| {ctx} | {shown} | {status} |")
        out.append("")
        out.append("## Sources cited in `model/` whose identifier no test repeats\n")
        if unasserted_model:
            out.append("A paper justifying a parameter with nothing checking it is "
                       "the citation form of \"documented mechanism, silently "
                       "inert\" — this repository's most frequent defect class. "
                       "Each of these is a candidate test, not necessarily a "
                       "defect.\n")
            out.append("**READ THE HEADING LITERALLY.** This tool matches PMIDs "
                       "and DOIs, so a test that names a paper in prose WITHOUT "
                       "its identifier is invisible here and its source lands in "
                       "this list. One such case is known (Schipke, named in a "
                       "test docstring with no PMID beside it). That is a defect "
                       "in the CITATION rather than necessarily in the coverage — "
                       "the project's own rule is that a test carries the DOI or "
                       "PMID of the source it asserts — but it means this list is "
                       "an UPPER BOUND on genuinely untested sources.\n")
            for label, rec, _a in unasserted_model:
                out.append(f"- **{label}** — {rec['context']} "
                           f"({', '.join(sorted(rec['model_files']))})")
        else:
            out.append("None. Every source cited in `model/` has at least one "
                       "test naming it.")
        out.append("")
        out.append("## What this index cannot see\n")
        out.append("Papers read and set aside without producing a test exist only "
                   "in the project's lab notebook, which is not published. Those "
                   "belong in a short hand-written *consulted, not asserted* list "
                   "in the manuscript. This tool states that gap rather than "
                   "hiding it.")
    else:
        for label, rec, asserted in rows:
            out.append(f"\n{label}")
            out.append(f"  context : {rec['context']}")
            if rec["model_files"]:
                out.append(f"  model   : {', '.join(sorted(rec['model_files']))}")
            if rec["tests"]:
                for n, ms in rec["tests"]:
                    out.append(f"  test    : {n}" + (f"   [{', '.join(ms)}]" if ms else ""))
            else:
                out.append("  test    : NONE — parameter justification only")
        out.append(f"\n{len(rows)} sources shown.")
        if unasserted_model:
            out.append(f"{len(unasserted_model)} cited in model/ with no test.")
    return "\n".join(out) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--markdown", action="store_true")
    ap.add_argument("--unasserted", action="store_true",
                    help="only sources cited in model/ that no test asserts")
    args = ap.parse_args()
    sys.stdout.write(render(collect(), args.markdown, args.unasserted))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
