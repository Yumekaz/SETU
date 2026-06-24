# GRU Training Report — Phase 3

## Data honesty (Hormuz-heavy cache)

The GDELT backtest cache contains ~55 Hormuz-window events. BAB_EL_MANDEB and MALACCA have thin daily series; those corridors use `TREND_FALLBACK` when below MIN_TRAIN_DAYS or variance threshold. This is directional evidence, not statistically proven accuracy.

- Total feature rows: 450
- HORMUZ rows: 150

## Corridor routing

- GRU corridors: BAB_EL_MANDEB, HORMUZ, MALACCA
- TREND_FALLBACK corridors: OTHER

## Final metrics

- Training data through: 2026-05-16
- Final train loss: 0.002607
- Final val loss: 0.002178

## Loss curve (epoch, train_loss, val_loss)

| epoch | train_loss | val_loss |
|---:|---:|---:|
| 0 | 0.200938 | 0.200163 |
| 4 | 0.018821 | 0.015412 |
| 8 | 0.017844 | 0.012483 |
| 12 | 0.017661 | 0.011326 |
| 16 | 0.017588 | 0.010715 |
| 20 | 0.017522 | 0.010411 |
| 24 | 0.017375 | 0.010217 |
| 28 | 0.016202 | 0.009389 |
| 32 | 0.014262 | 0.007480 |
| 36 | 0.013294 | 0.008080 |
| 40 | 0.010007 | 0.006923 |
| 44 | 0.010351 | 0.004384 |
| 48 | 0.007495 | 0.005197 |
| 52 | 0.005017 | 0.003912 |
| 56 | 0.004276 | 0.003131 |
| 60 | 0.003190 | 0.002821 |
| 64 | 0.003704 | 0.002538 |
| 68 | 0.003143 | 0.002522 |
| 72 | 0.003218 | 0.002654 |
| 76 | 0.002740 | 0.002503 |

## Band approach

Quantile pinball loss (p10/p50/p90) with sigmoid-bounded scores.
