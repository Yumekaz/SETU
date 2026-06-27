# SETU Known Limitations (Phase 7)

Explicit deferrals per SRS Section 17 triage. These are conscious scope boundaries, not silent gaps.

| ID | Limitation | Rationale |
|----|------------|-----------|
| KL-01 | Non-English source text not supported | MVP filters at ingest; rejected in `test_extraction.py` |
| KL-02 | AIS vessel tracking | Out of scope per SRS Phase 1 |
| KL-03 | Refined products (petrol/diesel) modeling | Stops at crude throughput per SRS Phase 2 |
| KL-04 | Long-horizon (>7 day) forecasting | GRU limited to 7-day band per SRS Phase 3 |
| KL-05 | Second historical backtest crisis | N=1 Hormuz case only per SRS Phase 5/7 |
| KL-06 | Mobile-responsive layout | Demo targets 1280px+ projector per SRS Phase 6 |
| KL-07 | Multi-presenter real-time sync | Single SQLite + polling sufficient for demo |
| KL-08 | Demo-day personnel / time-slot risks | Operational, not code-hardening |
| KL-09 | Literal kill -9 mid-request chaos | Simulated via connection refused / corrupt files |
| KL-10 | Social media sentiment analysis | Out of scope per SRS Phase 1 |