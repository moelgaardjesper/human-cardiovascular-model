#!/usr/bin/env python3
"""Check a freeze artefact against its own manifest.

    python3 tools/verify_freeze.py freeze/v1.0.0

A manifest full of sha256 hashes that nobody can check is decoration. This is
the checker, so a reader can confirm the artefact they downloaded is the one
that was published — and so we can confirm an edit to the artefact did not
silently invalidate it.

It also refuses an artefact containing a LOCAL FILESYSTEM PATH. The first
v1.0.0 emission wrote an absolute /home/<user>/... path into the manifest and
into the imported overnight run, which would have published a username and an
internal job id. That was caught by a pre-publication scan rather than by any
tooling, which is exactly the kind of check that should not depend on someone
remembering to look.
"""
import hashlib
import os
import re
import sys

ROW = re.compile(r"\| `([^`]+)` \| `([0-9a-f]{64})` \|")
LOCAL_PATH = re.compile(r"(/home/|/Users/|[A-Za-z]:\\\\|/root/)")


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def main(d):
    mp = os.path.join(d, "MANIFEST.md")
    if not os.path.isfile(mp):
        print(f"no MANIFEST.md in {d}", file=sys.stderr)
        return 2
    manifest = open(mp, encoding="utf-8").read()

    problems = 0
    listed = set()
    for name, want in ROW.findall(manifest):
        listed.add(name)
        p = os.path.join(d, name)
        if not os.path.isfile(p):
            print(f"  MISSING   {name}")
            problems += 1
            continue
        got = sha256(p)
        ok = got == want
        print(f"  {'ok       ' if ok else 'MISMATCH '} {name}")
        problems += (not ok)

    # Files present but not listed: an artefact should describe itself fully.
    for fn in sorted(os.listdir(d)):
        if fn != "MANIFEST.md" and fn not in listed:
            print(f"  UNLISTED  {fn}")
            problems += 1

    # Nothing published may carry a local filesystem path.
    for fn in sorted(os.listdir(d)):
        p = os.path.join(d, fn)
        try:
            text = open(p, encoding="utf-8", errors="ignore").read()
        except OSError:
            continue
        for m in LOCAL_PATH.finditer(text):
            line = text[:m.start()].count("\n") + 1
            print(f"  LOCAL PATH {fn}:{line} — {m.group(1)!r}")
            problems += 1

    print(f"\n{len(listed)} files listed, {problems} problem(s).")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1] if len(sys.argv) > 1 else "freeze/v1.0.0"))
