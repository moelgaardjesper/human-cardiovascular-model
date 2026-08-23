#!/usr/bin/env python3
"""
Stage 1 of the item-20 diagnostic: where does every parameter come from, and
does anything actually constrain it?

The venous-rebuild episode and backlog item 20 share a shape: a parameter that
no test constrains drifts to whatever value satisfies the parameters that ARE
constrained, and the error only surfaces years later through a downstream
symptom. This script makes that visible before it happens again.

For every named constant and every compartment field it reports:

  PROVENANCE  sourced   - a DOI, PMID or Author-Year appears in the surrounding
                          comment block
              described - commented, but no citation
              bare      - no explanatory comment at all
  CONSTRAINED whether the parameter's name appears anywhere in tests/

The dangerous quadrant is (bare or described) AND unconstrained: free to drift,
with nothing to catch it. Note the converse is NOT reassuring — "constrained"
only means a test mentions the name, not that the test would fail if the value
were wrong.

    python3 tools/parameter_audit.py            # summary + the risky quadrant
    python3 tools/parameter_audit.py --all      # every parameter

Static analysis only. Runs no simulation and changes nothing.
"""
import argparse
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL = os.path.join(ROOT, "model")
TESTS = os.path.join(ROOT, "tests")

# A citation looks like a DOI, a PMID, or "Surname 1998" / "Surname et al 2002".
CITATION = re.compile(
    r"(10\.\d{4,}/\S+|PMID[:\s]*\d+|PMC\d+|\b[A-Z][a-z]{2,}\s+(?:et\s+al\.?\s+)?(?:&\s+[A-Z][a-z]+\s+)?(?:19|20)\d{2}\b)")
CONST = re.compile(r"^([A-Z][A-Z0-9_]{2,})\s*=\s*(.+?)(?:\s*#.*)?$")
COMPARTMENT = re.compile(r'^\s*Compartment\("([a-z_]+)",\s*(.+?)\),?\s*(?:#.*)?$')

# Positional fields of the Compartment constructor, in order.
COMP_FIELDS = ["compliance", "resistance", "unstressed_volume", "height_m",
               "init_volume"]


def comment_block_above(lines, idx, max_lines=14):
    """Contiguous comment / docstring lines immediately above `idx`."""
    out = []
    i = idx - 1
    while i >= 0 and len(out) < max_lines:
        s = lines[i].strip()
        if s.startswith("#") or (s and not s[0].isalpha() and '"""' in s):
            out.append(s)
            i -= 1
        elif s == "":
            # A single blank line does not break a block; two do.
            if i - 1 >= 0 and lines[i - 1].strip().startswith("#"):
                i -= 1
                continue
            break
        else:
            break
    return "\n".join(reversed(out))


def classify(context):
    if not context.strip():
        return "bare"
    return "sourced" if CITATION.search(context) else "described"


def scan_model():
    """(name, file, line, value, provenance, context) for every parameter."""
    found = []
    for fname in sorted(os.listdir(MODEL)):
        if not fname.endswith(".py") or fname == "__init__.py":
            continue
        path = os.path.join(MODEL, fname)
        with open(path) as fh:
            lines = fh.read().splitlines()

        for n, line in enumerate(lines):
            m = CONST.match(line)
            if m and not line.startswith(" "):
                name, value = m.group(1), m.group(2).strip()
                if value.startswith(("{", "[", "(")) and len(value) > 60:
                    continue                      # big literal tables, skip
                ctx = comment_block_above(lines, n) + " " + (
                    line.split("#", 1)[1] if "#" in line else "")
                found.append((name, fname, n + 1, value, classify(ctx), ctx))
                continue

            c = COMPARTMENT.match(line)
            if c:
                cname, rest = c.group(1), c.group(2)
                parts = [p.strip() for p in rest.split(",")]
                inline = line.split("#", 1)[1] if "#" in line else ""
                ctx = comment_block_above(lines, n) + " " + inline
                prov = classify(ctx)
                for k, field in enumerate(COMP_FIELDS):
                    if k < len(parts):
                        found.append((f"{cname}.{field}", fname, n + 1,
                                      parts[k], prov, ctx))
    return found


def test_corpus():
    blob = []
    for fname in sorted(os.listdir(TESTS)):
        if fname.endswith(".py"):
            with open(os.path.join(TESTS, fname)) as fh:
                blob.append(fh.read())
    return "\n".join(blob)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true")
    args = ap.parse_args()

    params = scan_model()
    tests = test_corpus()

    rows = []
    for name, fname, line, value, prov, _ctx in params:
        base = name.split(".")[0]
        field = name.split(".")[-1]
        # A compartment field counts as mentioned only if BOTH the compartment
        # and the field name appear; the compartment name alone means nothing.
        if "." in name:
            constrained = (base in tests) and (field in tests)
        else:
            constrained = name in tests
        rows.append((name, fname, line, value, prov, constrained))

    total = len(rows)
    by_prov = {}
    for _, _, _, _, prov, _c in rows:
        by_prov[prov] = by_prov.get(prov, 0) + 1
    n_constrained = sum(1 for r in rows if r[5])

    print(f"{total} parameters across {len(set(r[1] for r in rows))} modules\n")
    print("  provenance:")
    for k in ("sourced", "described", "bare"):
        v = by_prov.get(k, 0)
        print(f"    {k:10s} {v:4d}  ({100*v/total:.0f}%)")
    print(f"\n  name appears in tests/: {n_constrained} ({100*n_constrained/total:.0f}%)")

    risky = [r for r in rows if r[4] != "sourced" and not r[5]]
    print(f"\n{'='*74}")
    print(f"RISKY QUADRANT — no citation AND unconstrained: {len(risky)} parameters")
    print(f"{'='*74}")
    for name, fname, line, value, prov, _c in sorted(risky, key=lambda r: (r[1], r[0])):
        print(f"  {prov:9s} {fname}:{line:<5d} {name:34s} = {value}")

    if args.all:
        print(f"\n{'='*74}\nALL PARAMETERS\n{'='*74}")
        for name, fname, line, value, prov, con in sorted(rows, key=lambda r: (r[1], r[0])):
            flag = "constrained" if con else "FREE"
            print(f"  {prov:9s} {flag:11s} {fname}:{line:<5d} {name:34s} = {value}")


if __name__ == "__main__":
    main()
