# GRU Training Report — Phase 3

## Data honesty (Hormuz-heavy cache)

The GDELT backtest cache contains ~55 Hormuz-window events. BAB_EL_MANDEB and MALACCA have thin daily series; those corridors use `TREND_FALLBACK` when below MIN_TRAIN_DAYS or variance threshold. This is directional evidence, not statistically proven accuracy.

- Total feature rows: 600
- HORMUZ rows: 150

## Corridor routing

- GRU corridors: BAB_EL_MANDEB, HORMUZ, MALACCA
- TREND_FALLBACK corridors: OTHER

## Final metrics

- Training data through: 2026-05-16
- Final train loss: 0.003701
- Final val loss: 0.002626

## Loss curve (epoch, train_loss, val_loss)

| epoch | train_loss | val_loss |
|---:|---:|---:|
| 0 | 0.201336 | 0.199342 |
| 4 | 0.018725 | 0.015722 |
| 8 | 0.017838 | 0.012592 |
| 12 | 0.017651 | 0.011413 |
| 16 | 0.017562 | 0.010818 |
| 20 | 0.017387 | 0.010489 |
| 24 | 0.016230 | 0.009389 |
| 28 | 0.015908 | 0.009702 |
| 32 | 0.014618 | 0.008036 |
| 36 | 0.014000 | 0.007798 |
| 40 | 0.011802 | 0.007836 |
| 44 | 0.008901 | 0.006910 |
| 48 | 0.008671 | 0.006622 |
| 52 | 0.007865 | 0.005415 |
| 56 | 0.008884 | 0.004715 |
| 60 | 0.007165 | 0.005668 |
| 64 | 0.005361 | 0.004593 |
| 68 | 0.004219 | 0.003462 |
| 72 | 0.003873 | 0.002777 |
| 76 | 0.003496 | 0.002482 |

## Band approach

Quantile pinball loss (p10/p50/p90) with sigmoid-bounded scores.

## Validation methodology

Validation windows use origins in the val partition with 14-day lookback spanning the full chronological timeline (including train dates), matching production inference semantics.
