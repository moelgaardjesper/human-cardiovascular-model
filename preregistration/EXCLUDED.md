# Excluded studies — and the mechanical reason

Studies supplied for the blind phase that the model cannot be asked, or that
are not out-of-sample.

**This list is a result.** It maps the architecture's boundary using real
published protocols rather than the authors' own account of the model's limits,
which a reader has more reason to trust. A model that could attempt everything
would be one whose limits nobody had tested.

| # | study | identifier | reason | category |
|---|---|---|---|---|

## Categories

- **IN-SAMPLE** — already cited in `model/` or `tests/`; was available during
  development, so it cannot test anything. Detected by
  `tools/check_insample.py`, not by memory. *(Likhvantsev 2025 is the known
  example: used from the beginning, so unavailable for this phase.)*
- **NO MECHANISM** — the model lacks the structure the protocol requires. Name
  it: no cellular compartment, no 1-D wave propagation, no skeletal-muscle
  pump, no age-dependent baroreflex, no pregnancy or sepsis physiology.
- **OUT OF VALIDATED RANGE** — mechanically runnable but outside the envelope
  where outputs mean anything, e.g. posture beyond −30°/+45°.
- **NO COMPARABLE OUTPUT** — the model runs the protocol but reports nothing
  that corresponds to what was measured, and no convention mapping exists.
  Distinct from CONVENTION, where a mapping exists but differs.
- **RESULT SEEN** — the result reached the model author before registration.
  Excluded regardless of everything else, and recorded rather than hidden.
