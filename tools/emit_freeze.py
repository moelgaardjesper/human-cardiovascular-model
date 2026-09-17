#!/usr/bin/env python3
"""
Emit the frozen artefact: everything a reader needs to reproduce this model's
published numbers, from ONE command.

    python3 tools/emit_freeze.py --tag v1.0.0

WHY THIS EXISTS. A paper that says "the model gives 95.4 mmHg" is not
reproducible. A reader needs the parameter set that produced it, the library
versions it was computed with, the interpreter, the commit, and the actual
output of the test suite at that commit — and needs them as ONE consistent
snapshot rather than as figures scattered through a manuscript and a repo whose
HEAD has since moved.

WHAT IT WRITES, into freeze/<tag>/:

    MANIFEST.md          what this is, what ran, what did NOT, sha256 of each file
    environment.txt      interpreter, platform, full pip freeze
    parameters.md        every compartment field and every model constant,
                         INTROSPECTED from the modules — not a typed list
    validation_table.md  literature target vs model value, measured fresh
    suite_fast.txt       pytest            (the ratchet; what CI runs)
    suite_slow.txt       pytest -m slow    (minutes-to-hours dynamics)
    suite_overnight.txt  pytest -m overnight (24 h runs, ~11 h wall clock)

THE PARAMETER DUMP IS INTROSPECTED ON PURPOSE. A hand-written list of fields to
report is the same construct that silently dropped `p_stiffen` from patient
scaling for months: a list that stops matching what produces it, with nothing
to notice. This walks the dataclass fields and the module namespaces instead, so
a parameter added tomorrow appears here without anyone remembering to add it.

WHAT IT DELIBERATELY DOES NOT INCLUDE. `docs/reference_values.md` and
`docs/validation_log.md` are the project's lab notebook and are not published.
The artefact carries EVIDENCE — quantity, source, cohort, model value — and not
the working. Nothing here reads either file.

A DIRTY WORKING TREE IS REFUSED. An artefact emitted from uncommitted code
cannot be checked out again, which defeats the entire purpose. Override with
--allow-dirty only for a dry run you intend to throw away.
"""
import argparse
import hashlib
import os
import platform
import subprocess
import sys
import textwrap
from dataclasses import fields as dataclass_fields
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)


def sh(cmd, **kw):
    """Run a command, returning (exit_code, combined_output)."""
    p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, **kw)
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def git(*args):
    _, out = sh(["git", *args])
    return out.strip()


# ---------------------------------------------------------------------------
# Parameter dump — introspected, never typed
# ---------------------------------------------------------------------------

# Modules whose module-level constants are part of the frozen model. Private
# names (leading underscore) are included: _TAU_SYMP_SLOW is as much a model
# parameter as MAP_SETPOINT, and hiding it would make the artefact incomplete
# in exactly the direction that matters.
_CONSTANT_MODULES = ("model.heart", "model.baroreflex", "model.respiration",
                     "model.gravity", "model.circulation", "model.slow_dynamics",
                     "model.aging", "model.patient", "model.perfusion",
                     "model.pharmacology", "model.compartments")


def _is_parameter(name, value):
    """A module-level constant that belongs in the artefact."""
    if name.startswith("__"):
        return False
    if not isinstance(value, (int, float, bool, str, tuple)):
        return False
    if isinstance(value, str) and (len(value) > 120 or "\n" in value):
        return False          # a docstring or a path, not a parameter
    if isinstance(value, tuple):
        # Sourced lookup tables (age relations) are parameters; anything else
        # tuple-shaped is almost certainly plumbing.
        return all(isinstance(x, (int, float, tuple)) for x in value) and len(value) <= 40
    return name.upper() == name or name.startswith("_")


def dump_parameters():
    import importlib
    from model.compartments import default_compartments

    out = []
    out.append("# Frozen parameter set\n")
    out.append("Introspected from the modules at the freeze commit — not a "
               "transcribed list.\nA parameter added to the model appears here "
               "without anyone editing this tool.\n")

    # --- compartments ------------------------------------------------------
    comps = default_compartments()
    names = [f.name for f in dataclass_fields(comps[0])]
    out.append(f"\n## The {len(comps)} compartments\n")
    out.append("Fields are every field of the `Compartment` dataclass, in "
               "declaration order.\n")
    out.append("| idx | " + " | ".join(names) + " |")
    out.append("|" + "---|" * (len(names) + 1))
    for i, c in enumerate(comps):
        cells = []
        for n in names:
            v = getattr(c, n, None)
            cells.append("—" if v is None else (f"{v:g}" if isinstance(v, float) else str(v)))
        out.append(f"| {i} | " + " | ".join(cells) + " |")

    total_v = sum(getattr(c, "init_volume", 0.0) or 0.0 for c in comps)
    total_u = sum(getattr(c, "unstressed_volume", 0.0) or 0.0 for c in comps)
    out.append(f"\nTotal initial volume **{total_v:.1f} mL**, of which "
               f"**{total_u:.1f} mL** unstressed "
               f"({100.0 * total_u / total_v:.1f} %) and "
               f"**{total_v - total_u:.1f} mL** stressed "
               f"({100.0 * (total_v - total_u) / total_v:.1f} %).\n")

    # --- module constants --------------------------------------------------
    #
    # A constant imported into another module (circulation does `from .heart
    # import LV_EMAX`) is indistinguishable from one defined there, because a
    # float carries no __module__. Listing it twice would read as if the model
    # held two independent copies — which is a real defect this project has had
    # (item 50: the reference operating point typed twice, and the copies had
    # drifted). So a repeat is LABELLED as a re-export rather than dropped:
    # hiding it would lose the information that circulation reads that value.
    out.append("\n## Model constants, by module\n")
    out.append("A constant that first appears in an earlier module and is "
               "imported by a later one is marked *re-export*. The model holds "
               "ONE definition; the label tells you which module owns it.\n")
    seen = {}
    for modname in _CONSTANT_MODULES:
        try:
            mod = importlib.import_module(modname)
        except Exception as exc:                          # noqa: BLE001
            out.append(f"\n### {modname}\n\nIMPORT FAILED: {exc}\n")
            continue
        rows = []
        for name in sorted(vars(mod)):
            value = vars(mod)[name]
            if getattr(value, "__module__", modname) != modname and not isinstance(
                    value, (int, float, bool, str, tuple)):
                continue
            if _is_parameter(name, value):
                rows.append((name, value))
        if not rows:
            continue
        out.append(f"\n### `{modname}`\n")
        out.append("| constant | value |")
        out.append("|---|---|")
        for name, value in rows:
            shown = f"{value:g}" if isinstance(value, float) else repr(value)
            if len(shown) > 200:
                shown = shown[:197] + "..."
            owner = seen.get(name)
            if owner is None:
                seen[name] = (modname, value)
                note = ""
            elif owner[1] == value:
                note = f" *(re-export from `{owner[0]}`)*"
            else:
                # Two modules hold the same NAME with DIFFERENT values. That is
                # the item-50 defect shape and the artefact must shout about it.
                note = (f" **DIVERGENT COPY — `{owner[0]}` has "
                        f"{owner[1]!r}. Two definitions of one constant.**")
            out.append(f"| `{name}` | {shown}{note} |")
    return "\n".join(out) + "\n"


# ---------------------------------------------------------------------------

def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tag", required=True,
                    help="release tag this artefact belongs to, e.g. v1.0.0")
    ap.add_argument("--out", default=None, help="output directory (default freeze/<tag>)")
    ap.add_argument("--allow-dirty", action="store_true",
                    help="emit from an uncommitted tree — dry runs only")
    ap.add_argument("--skip-fast", action="store_true",
                    help="dry runs only — the fast suite IS the ratchet "
                         "and a published artefact must contain it")
    ap.add_argument("--skip-slow", action="store_true")
    ap.add_argument("--skip-overnight", action="store_true",
                    help="the overnight tier is ~11 h of wall clock")
    ap.add_argument("--overnight-from", metavar="PATH",
                    help="IMPORT an overnight run captured separately instead of "
                         "spending 11 h re-running it. The file is copied in "
                         "verbatim and the manifest records that it was imported "
                         "rather than produced by this invocation, WITH the "
                         "commit it was run at, so a reader can tell the "
                         "difference. Emitting an 11 h result requires starting "
                         "it before the freeze commit exists; pretending "
                         "otherwise would be the dishonest option.")
    ap.add_argument("--skip-table", action="store_true")
    args = ap.parse_args()

    # THE ARTEFACT DIRECTORY IS NOT "DIRTY WORK". Its own output lives under
    # freeze/, so a second run saw the first run's files in `git status` and
    # refused — the tool could not be run twice. Only changes OUTSIDE the
    # artefact tree mean the code being described is uncommitted.
    out_rel = os.path.relpath(args.out or os.path.join(ROOT, "freeze", args.tag), ROOT)
    dirty = "\n".join(l for l in git("status", "--porcelain").splitlines()
                      if out_rel not in l and "freeze/" not in l)
    if dirty and not args.allow_dirty:
        print("REFUSING: the working tree is dirty. An artefact emitted from "
              "uncommitted code cannot be checked out again, which defeats its "
              "purpose. Commit first, or pass --allow-dirty for a throwaway "
              "dry run.\n\n" + dirty, file=sys.stderr)
        return 2

    out_dir = args.out or os.path.join(ROOT, "freeze", args.tag)
    os.makedirs(out_dir, exist_ok=True)

    written = []

    def write(name, text):
        path = os.path.join(out_dir, name)
        with open(path, "w") as fh:
            fh.write(text)
        written.append(name)
        print(f"  wrote {name} ({len(text)} bytes)")
        return path

    commit = git("rev-parse", "HEAD")
    started = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    print(f"Emitting freeze artefact for {args.tag} at {commit[:12]} -> {out_dir}")

    # --- environment -------------------------------------------------------
    _, pipfreeze = sh([sys.executable, "-m", "pip", "freeze"])
    write("environment.txt", textwrap.dedent(f"""\
        Frozen environment
        ==================
        emitted        {started}
        tag            {args.tag}
        commit         {commit}
        tree state     {'DIRTY (dry run)' if dirty else 'clean'}

        interpreter    {sys.version}
        executable     {sys.executable}
        platform       {platform.platform()}
        machine        {platform.machine()}

        DETERMINISM. The model contains no random number generation anywhere:
        the same inputs produce bit-identical outputs on the same environment.
        Differences across environments, if any, come from the libraries below
        and from floating-point behaviour, which is why they are pinned.

        pip freeze
        ----------
        """) + pipfreeze)

    # --- parameters --------------------------------------------------------
    print("  introspecting parameters...")
    write("parameters.md", dump_parameters())

    # --- validation table --------------------------------------------------
    if not args.skip_table:
        print("  measuring validation table (several minutes)...")
        # STDOUT ONLY. validation_table.py writes per-row progress to stderr,
        # and merging the streams appended "running: ..." lines to the published
        # table. A published artefact must not carry the tool's own chatter.
        p = subprocess.run([sys.executable, "tools/validation_table.py", "--markdown"],
                           cwd=ROOT, capture_output=True, text=True)
        code, out = p.returncode, p.stdout
        if code:
            out += "\n\nTOOL STDERR\n-----------\n" + (p.stderr or "")
        write("validation_table.md",
              f"# Validation table — {args.tag} ({commit[:12]})\n\n"
              f"Measured fresh at the freeze commit by "
              f"`tools/validation_table.py --markdown`.\n\n"
              f"**THIS TABLE IS REPRESENTATIVE, NOT EXHAUSTIVE.** It holds the "
              f"first literature that went into the model, kept as a readable "
              f"summary. It is NOT the evidence base and a reader should not "
              f"count its rows as the validation. **`suite_fast.txt`, "
              f"`suite_slow.txt` and `suite_overnight.txt` in this directory are "
              f"the complete record** — every assertion, every cited source, "
              f"every strict xfail. Carrying every paper and how each was used "
              f"would make reading the table a project in itself.\n\n"
              f"Where a source records its cohort's age the row says so and the "
              f"model is run at that age. Where it does not, the row says that "
              f"too: an unmatched comparison shown as matched is how a "
              f"generation gap gets read as a model error.\n\n"
              f"Rows in the second table are measured by the slow suite and are "
              f"TRANSCRIBED WITH THEIR DATE, not re-measured by this tool — "
              f"`suite_slow.txt` is the actual run.\n\n"
              + out + (f"\n\n(tool exited {code})\n" if code else "\n"))

    # --- source index ------------------------------------------------------
    # DERIVED, so it costs nothing to keep and cannot drift. The curated
    # validation table beside it is representative and short enough to read;
    # this is the complete citation record, generated from the identifiers
    # already written into the suite.
    print("  building source index...")
    p = subprocess.run([sys.executable, "tools/source_index.py", "--markdown"],
                       cwd=ROOT, capture_output=True, text=True)
    write("sources.md", p.stdout if p.returncode == 0 else
          f"# Source index\n\nTOOL FAILED (exit {p.returncode})\n\n{p.stderr}")

    # --- the three test tiers ----------------------------------------------
    tiers = [("suite_fast.txt", ["-q"], "fast suite — the ratchet; what CI runs",
              not args.skip_fast)]
    tiers.append(("suite_slow.txt", ["-q", "-m", "slow"],
                  "slow-dynamics suite", not args.skip_slow))
    tiers.append(("suite_overnight.txt", ["-q", "-m", "overnight"],
                  "overnight tier (~11 h wall clock)", not args.skip_overnight))

    ran = {}
    imported = {}
    if args.overnight_from:
        raw = open(args.overnight_from, encoding="utf-8", errors="replace").read()
        # BASENAME ONLY. The full path is a LOCAL FILESYSTEM PATH and this file
        # gets published: the first emission wrote
        # "/home/<user>/.claude/jobs/<id>/tmp/..." into both the manifest and the
        # imported file, leaking a username and an internal job id into a public
        # artefact. The basename is all a reader can use anyway — they cannot
        # open a path on someone else's machine — and the provenance that
        # matters (the commit, and the AST check) lives inside the file.
        src_label = os.path.basename(args.overnight_from)
        write("suite_overnight.txt",
              f"# overnight tier (~11 h wall clock) — IMPORTED, not run here\n"
              f"# source: {src_label}\n"
              f"# imported into the {args.tag} artefact at {started}\n"
              f"# An 11 h run must be started BEFORE the freeze commit exists,\n"
              f"# so its provenance is stated in the source file's own header\n"
              f"# rather than inferred here.\n\n"
              + raw)
        ran["suite_overnight.txt"] = "IMPORTED"
        imported["suite_overnight.txt"] = src_label
        tiers = [t for t in tiers if t[0] != "suite_overnight.txt"]

    for name, flags, label, do_run in tiers:
        if not do_run:
            ran[name] = "SKIPPED"
            print(f"  skipping {label}")
            continue
        print(f"  running {label} ...")
        code, out = sh([sys.executable, "-m", "pytest", *flags])
        ran[name] = f"exit {code}"
        write(name, f"# {label}\n# {args.tag}  {commit}\n"
                    f"# command: pytest {' '.join(flags)}\n\n{out}")

    # --- manifest ----------------------------------------------------------
    lines = [f"# Freeze artefact — {args.tag}", "",
             f"- commit `{commit}`",
             f"- emitted {started}",
             f"- interpreter {platform.python_version()}",
             f"- tree {'DIRTY — DRY RUN, DO NOT PUBLISH' if dirty else 'clean'}",
             "",
             "Regenerate with:", "", f"    python3 tools/emit_freeze.py --tag {args.tag}",
             "",
             "## What ran", ""]
    for name, _flags, label, _do in tiers:
        lines.append(f"- {label}: **{ran.get(name, 'not attempted')}**")
    for name, srcpath in imported.items():
        lines.append(f"- `{name}`: **IMPORTED** from `{srcpath}` — run separately, "
                     f"not produced by this invocation. The commit it ran at is "
                     f"recorded inside the file.")
    lines += ["",
              "## What is NOT here, deliberately", "",
              "`docs/reference_values.md` and `docs/validation_log.md` are the "
              "project's lab notebook and are not published. This artefact "
              "carries the evidence — quantity, source, cohort, model value — "
              "and not the working.",
              "",
              "## Files", "",
              "| file | sha256 |", "|---|---|"]
    for name in written:
        lines.append(f"| `{name}` | `{sha256(os.path.join(out_dir, name))}` |")
    write("MANIFEST.md", "\n".join(lines) + "\n")

    print(f"\nDone. {len(written)} files in {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
