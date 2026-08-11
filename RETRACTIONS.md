# Dropped references

Sources removed after verification failed. Kept short and in one place on purpose:
restating a bad claim spreads it. Detail, where any is needed, is in the (untracked)
validation log.

| Date | Reference | Action |
|---|---|---|
| 2026-08-10 | Lister 1963 (PMID 14067514), cited as a second anchor for `Kf` | Paper contains no filtration coefficient. Citation dropped; `Kf = 6.7` rests on Guyton alone. Lister retained for the refill trajectory, which it does report. |
| 2026-08-11 | Ref `[10]`, PEEP / cardiac output | Identifiers did not resolve and the numeric target was unverified. Replaced with Jardin 1981, N Engl J Med 304:387-92 (PMID 7005679). Numeric target removed, not re-attached — the test asserts direction and dose-response only. |

Commits are not rewritten. Corrections are made forward.

**Rule** (`CLAUDE.md`, "Validation discipline"): do not cite a paper whose numbers you have
not read. If the full text cannot be obtained, cite only what the verified abstract supports
and say so at the citation.

All 19 PMIDs in tracked files were checked against PubMed on 2026-08-11; one mismatch, above.
