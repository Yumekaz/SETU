# GRU Training Report — Phase 3

## Data honesty (Hormuz-heavy cache)

The GDELT backtest cache contains ~55 Hormuz-window events concentrated in the Hormuz corridor. Only HORMUZ is routed to the shared GRU; BAB_EL_MANDEB, MALACCA, and OTHER use `TREND_FALLBACK` (Phase 1 RISING/FALLING/STABLE). Do not treat thin-corridor outputs as statistically proven accuracy.

- Total feature rows: 600
- HORMUZ rows: 150

## Corridor routing

- GRU corridors: HORMUZ
- TREND_FALLBACK corridors: BAB_EL_MANDEB, MALACCA, OTHER

## Final metrics

- Training data through: 2026-05-16
- Final train loss: 0.014527
- Final val loss: 0.007427

## Loss curve (epoch, train_loss, val_loss)

| epoch | train_loss | val_loss |
|---:|---:|---:|
| 0 | 0.218607 | 0.238715 |
| 4 | 0.046865 | 0.047985 |
| 8 | 0.020391 | 0.018449 |
| 12 | 0.017981 | 0.014788 |
| 16 | 0.017219 | 0.013261 |
| 20 | 0.016899 | 0.012226 |
| 24 | 0.016705 | 0.011519 |
| 28 | 0.016592 | 0.010961 |
| 32 | 0.016513 | 0.010564 |
| 36 | 0.016441 | 0.010242 |
| 40 | 0.016407 | 0.009959 |
| 44 | 0.016378 | 0.009736 |
| 48 | 0.016331 | 0.009589 |
| 52 | 0.016272 | 0.009481 |
| 56 | 0.016170 | 0.009337 |
| 60 | 0.016075 | 0.009160 |
| 64 | 0.015869 | 0.008902 |
| 68 | 0.015661 | 0.008576 |
| 72 | 0.015391 | 0.008227 |
| 76 | 0.015000 | 0.007843 |

## Band approach

Quantile pinball loss (p10/p50/p90) with sigmoid-bounded scores.

## Validation methodology

Validation windows use origins in the val partition with 14-day lookback spanning the full chronological timeline (including train dates), matching production inference semantics.
