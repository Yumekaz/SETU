# Hormuz Threshold Calibration — 2026-07-13

## Protocol

This is a separate calibration exercise, not a retrospective lowering of the
lead-time threshold. It uses only the pre-incident part of the dense cache:

| Parameter | Value |
|---|---|
| Calibration window | 2026-01-15 to 2026-01-31 |
| Evaluation window | 2026-02-01 to 2026-03-02 |
| Incident start used to separate windows | 2026-02-28 (timeline evidence) |
| Target daily false-positive rate | ≤5% |
| Alert rule | `score >= threshold` |
| Dataset | 2,753 date-bounded GDELT candidate rows / 1,080 normalized events after corridor-evidence and CAMEO gates |

The calibration window is held separate from the evaluation window. It is only
17 days long, so it is an exploratory calibration diagnostic rather than a
production-quality false-positive estimate.

## Result

The source-deduplicated noisy-OR scorer is no longer mechanically flat after
removing city-level UAE/Dubai false positives. Its 17 baseline daily scores
range from `0.0` to `0.437500`; the maximum occurs on 2026-01-24.

| Candidate threshold | Baseline alert rate | Operational? |
|---|---:|---|
| `0.437500` | 5.9% (1/17 days) | No — exceeds the ≤5% target |
| `0.437501` | 0% (0/17 days) | Yes — locked before final evaluation |

`cap_single_event=0.25` is applied to individual events/sources, then unique
sources are combined with noisy-OR. Consequently, corroborating sources can
raise the corridor score above the per-event cap without allowing a single
source to dominate.

## Decision

`0.437501` was locked on 2026-07-13 before the final Feb–Mar evaluation. The
final replay first crosses it on 2026-02-10 at 0.578125, yielding 20 days to
the 2026-03-02 reference point. This is N=1 evidence with a short baseline,
not a general accuracy estimate. The reproducible command is:

```powershell
.\backend\.venv\Scripts\python.exe scripts\calibrate_hormuz_threshold.py
```

Future calibration still requires longer, independent calm periods and multiple
untouched incident periods. See `docs/known_limitations.md` KL-11 for the
remaining place-name disambiguation limitation.
