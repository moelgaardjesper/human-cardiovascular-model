"""Reported, never asserted: where each literature test sits in units of its target's SPREAD.

The suite asserts most literature targets at 1 SD of individuals, because SE cannot be built for every
study. That asks whether the model is a plausible INDIVIDUAL; the model is meant to be the cohort's MEAN
patient, for which 1 SD is wide by about sqrt(n). So every literature test also records two numbers:

    z_sd = (model - mean) / sd             against the spread of individuals
    z_se = (model - mean) / (sd / sqrt n)  against the uncertainty of the group mean

z_se is REPORTED, NOT ASSERTED. A band built on SE alone fails for reasons that are not the model's
(studies disagree by more than their SEs; our cohort match is imperfect), so it would make a noisy
ratchet. Its job is to stop a 1 SD pass from hiding a mean that sits several SE away.

`sd` is the SD of the quantity AS COMPARED: of the paired change for a change, of the level for a level.
Where only an SE is published, pass it as `se=` and leave `sd` None. Where neither can be built, pass
None — the row is still listed, so a reader sees what is unscored rather than a silent gap.
The table is written to `scorecard.json` (path in SCORECARD_PATH) at the end of a run.
"""
import json
import math
import os

_ROWS = []
SCORECARD_PATH = os.environ.get("SCORECARD_PATH", "scorecard.json")


def score(test, quantity, model, mean, sd=None, n=None, se=None, kind="level", source=""):
    """Record one model-vs-literature comparison. Returns nothing and never raises on the numbers."""
    model, mean = float(model), float(mean)
    if se is None and sd is not None and n:
        se = sd / math.sqrt(n)
    z_sd = (model - mean) / sd if sd else None
    z_se = (model - mean) / se if se else None
    _ROWS.append(dict(test=test, quantity=quantity, kind=kind, source=source, model=model, mean=mean,
                      sd=sd, n=n, se=se, z_sd=z_sd, z_se=z_se))


def rows():
    return list(_ROWS)


def write(path=None):
    if not _ROWS:
        return None
    path = path or SCORECARD_PATH
    with open(path, "w") as fh:
        json.dump(sorted(_ROWS, key=lambda r: -abs(r["z_se"] or 0.0)), fh, indent=1)
    return path
