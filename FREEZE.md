# Model freeze

## What a freeze is, and why this project needs one

This model has changed every week of its life. Numbers quoted in a manuscript
must therefore name a *state*, not a repository — "the model gives MAP 95.4" is
meaningless six commits later, and a reader who clones `master` and disagrees
with a published figure has no way to tell whether they found an error or simply
a newer model.

A freeze fixes one state and gives it a name:

- **the code**, at a tagged commit;
- **the environment**, pinned exactly — interpreter and libraries;
- **the parameters**, dumped from the modules rather than transcribed;
- **the evidence**, as the actual output of the test suite at that commit.

Everything above is emitted by one command, so a reader can regenerate it and
compare byte for byte.

## Regenerating the artefact

```bash
python3 tools/emit_freeze.py --tag v1.0.0
```

It writes `freeze/<tag>/`:

| file | what it is |
|---|---|
| `MANIFEST.md` | what ran, what did not, sha256 of every file |
| `environment.txt` | interpreter, platform, full `pip freeze` |
| `parameters.md` | every compartment field and model constant, **introspected** |
| `validation_table.md` | literature target vs model value, measured fresh |
| `suite_fast.txt` | `pytest` — the ratchet, and what CI runs |
| `suite_slow.txt` | `pytest -m slow` — minutes-to-hours dynamics |
| `suite_overnight.txt` | `pytest -m overnight` — 24 h runs, ~11 h wall clock |

The command **refuses to run on a dirty working tree**. An artefact emitted from
uncommitted code cannot be checked out again, which defeats its purpose.

### The parameter dump is introspected, deliberately

It walks the `Compartment` dataclass fields and the module namespaces rather
than carrying a list of things to report. A hand-written list is the construct
that silently dropped `p_stiffen` from patient scaling for months: a list that
stops matching what produces it, with nothing to notice. A parameter added
tomorrow appears in the artefact without anyone remembering to add it.

It also **labels re-exports and shouts about divergent copies**. If two modules
hold the same constant name with different values, the dump says so in bold —
that is the shape of backlog item 50, where the reference operating point was
typed twice and the copies had drifted apart on CVP.

## The environment is part of the model

- **Python 3.14.4.** Development and every published measurement happened here.
  CI ran 3.13 until the freeze, which meant CI was not testing the environment
  the numbers came from.
- **3.13 is not claimed to work.** It is *untested at the freeze*, which is a
  different statement from *incompatible*. Only 3.14 was available on the
  development machine, so no honest claim about 3.13 could be made.
- `requirements.txt` pins exact versions, including the transitive tree —
  Flask's dependencies move independently of Flask, and a reproduction needs the
  whole set rather than the parts we import by name.

**Determinism:** the model contains no random number generation anywhere. Same
inputs, same environment, bit-identical outputs. Any difference a reader sees is
either their environment or a real disagreement, and the pins are what make
those two distinguishable.

## The three test tiers — quote all three or none

`pytest` alone runs the **fast suite** only. Seven `slow` tests and one
`overnight` test are deselected by `pytest.ini`, and quoting the fast count on
its own silently omits the entire minutes-to-hours arm of the model.

The `overnight` tier is a single 24 h simulation, about 11 hours of wall clock.
It is a **strict xfail** and it is the strongest result in the project: the
validation log recorded *in advance* that the model would undershoot Lister's
transcapillary refill because it has no cellular compartment, and it did — 41 %
of the deficit replaced at 24 h against a measured 50–80 %, while the 2 h test on
the same mechanism passes. A missing compartment predicts exactly that split; a
wrong coefficient would have broken both.

## What the artefact does NOT contain

`docs/reference_values.md` and `docs/validation_log.md` are the project's lab
notebook and are not published. They record provisional readings, premises later
withdrawn, and mistakes as they happened — deliberately, because that record is
what stops them being repeated — and read out of context a withdrawn premise
looks like a claim the project is making.

The artefact carries the **evidence**: quantity, source, cohort, model value,
deviation. Not the working. Nothing in `emit_freeze.py` reads either file.

## Known limitations at the freeze

These are carried as strict `xfail` tests, so none of them can close silently.
They are stated here because a frozen model that hides its gaps is worse than no
freeze at all.

- **Pulse pressure amplification is inverted.** Brachial PP must exceed central;
  the model reads 0.88 against a measured 1.33 ± 0.16. Amplification needs wave
  travel and reflection, which a lumped model does not have. Architectural.
- **No cellular compartment** — 24 h refill undershoots by design (above).
- **No active venous muscle pump** — validated posture range is −30° to +45°.
- **No 1-D wave propagation** — augmentation index and pulse wave velocity are
  not expressible at all.
- **The baroreflex has no age dependence.** Gain is identical at 25 and at 85,
  while human baroreflex sensitivity falls steeply with age. Gains are
  calibrated on a cohort of median age ~33 and applied unchanged to the
  55-year-old reference patient, so every reflex magnitude is a younger person's
  reflex. Direction of the error is known; magnitude is not.
- **Left atrial emptying fraction** 42.8 % against 61.1 ± 6.2 (−2.9 SD).
- **Phenylephrine pressor response** reaches two thirds of the measured MAP rise
  and half the resistance rise, and saturates below target. The *flow* response
  — cardiac output, heart rate and stroke volume — is in band.
- **The reference patient rescales itself by −14 %** when entered by its own
  measured haemodynamics.

## Cohort matching

Every literature comparison states its cohort's age, and the model is run at that
age wherever the mechanism admits one. Three cohorts are matched on age and body
size; four are matched on size only, because no age is recorded in the source.
The one place matching is impossible — the baroreflex — is listed above as a
limitation rather than passed over.
