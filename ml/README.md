# SETU ML

## Phase 1 — Signal extraction (llama-cpp-python)

- GBNF grammar: [`grammars/signal_event.gbnf`](grammars/signal_event.gbnf)
- Runner: [`extraction/llama_runner.py`](extraction/llama_runner.py)
- Download model: `python scripts/download_model.py`
- Set `SETU_LLM_MODEL_PATH` and `SETU_EXTRACTOR_MODE=llm` for Phi-3 extraction

When the model is absent, the backend uses the deterministic rules fallback in
`backend/app/signals/rules_extractor.py` (CI default).

## Phase 3 — GRU forecasting

```bash
python scripts/build_forecast_dataset.py
python scripts/train_gru.py
```

- Features: `backend/app/forecast/features.py` (14-day lookback)
- Model: `ml/forecast/gru_model.py`
- Checkpoint: `data/checkpoints/gru/model.pt`
- Report: `docs/gru_training_report.md`