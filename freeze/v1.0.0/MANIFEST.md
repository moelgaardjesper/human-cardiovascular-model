# Freeze artefact — v1.0.0

- commit `90cc1d0f2955b5a1e934bc128844985922d10d91`
- emitted 2026-09-16 19:35:29 UTC
- interpreter 3.14.4
- tree clean

Regenerate with:

    python3 tools/emit_freeze.py --tag v1.0.0

## What ran

- fast suite — the ratchet; what CI runs: **exit 0**
- slow-dynamics suite: **exit 0**
- `suite_overnight.txt`: **IMPORTED** from `overnight_annotated.txt` — run separately, not produced by this invocation. The commit it ran at is recorded inside the file.

## What is NOT here, deliberately

`docs/reference_values.md` and `docs/validation_log.md` are the project's lab notebook and are not published. This artefact carries the evidence — quantity, source, cohort, model value — and not the working.

## Files

| file | sha256 |
|---|---|
| `environment.txt` | `6b9845db222023d70e847a61090482a9d68b89d8ab700d114a1918687070ef70` |
| `parameters.md` | `eb65a041aa1b191e3c9bfc99f39a4991b2fbe7f4c6cc9bf8e5fe8869258fc829` |
| `validation_table.md` | `05086bb440ac15961dab7a810403b6f6153951aeb8c89c9efdb0524b4ef2a9e2` |
| `sources.md` | `88819d405fcc013e20ef68523715996a8d1f5eca231b521983938bc209508b69` |
| `suite_overnight.txt` | `967d33bdcb3cd163cc75616dd2f277c8f12043c93fe9290bb7cac21f8ab77cbb` |
| `suite_fast.txt` | `b3d666854789b90e344574d70e80607c66c947b92484daee89b9a800628c2046` |
| `suite_slow.txt` | `c5b21cb4da728f8df3d0b9e011872faeb24fce073ae18af26e653509dfab923e` |
