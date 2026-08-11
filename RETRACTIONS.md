# Dropped references

Sources removed after verification failed. Kept short and in one place on purpose:
restating a bad claim spreads it. Commit SHAs below give full traceability without
reproducing the text — a reviewer can see exactly where each reference entered the tree and
where it left. Detail, where any is needed, is in the (untracked) validation log.

## R1 — filtration coefficient attributed to Lister 1963

| | |
|---|---|
| Entered | `c2232a9` (2026-08-07) |
| Removed | `a37d96f` (2026-08-11) |
| Files | `model/slow_dynamics.py`, `tests/test_slow_dynamics.py` |
| Finding | The paper reports refill rates, percentages and plasma volumes. It contains no filtration coefficient. |
| Consequence | Citation dropped. `Kf = 6.7` rests on Guyton alone, with no independent human anchor. Lister 1963 (PMID 14067514) is retained for the refill trajectory, which it does report and which the model matches to within ~1.6x. |

## R2 — reference `[10]`, PEEP and cardiac output

| | |
|---|---|
| Entered | `17b5ce3` (2026-06-02); a further occurrence added in `36b5625` (2026-06-12) |
| Removed | `a37d96f` (2026-08-11) |
| Files | `model/respiration.py`, `tests/test_circulation.py` |
| Finding | The PMID resolved to an unrelated paper in another field, and the journal reference did not resolve at all. The numeric target attributed to it was unverifiable. |
| Consequence | Replaced with Jardin F et al. (1981) N Engl J Med 304:387-92, PMID 7005679, DOI 10.1056/NEJM198102123040703, verified against PubMed. The numeric target was removed, not re-attached: only the abstract has been read, so `test_peep_reduces_co_jardin1981` now asserts direction and dose-response only. |

## Notes for a reviewer

Each reference is present in the working tree at every commit from "Entered" up to (but not
including) "Removed". To see precisely what was taken out and what replaced it:

```
git show a37d96f
```

History is not rewritten. Correcting forward keeps the question "was this ever used, and
where?" answerable, and preserves the commit SHAs cited elsewhere in the project record.

**Rule** (`CLAUDE.md`, "Validation discipline"): do not cite a paper whose numbers you have
not read. If the full text cannot be obtained, cite only what the verified abstract supports
and say so at the citation.

All 19 PMIDs in tracked files were checked against PubMed on 2026-08-11; R2 was the only
mismatch.
