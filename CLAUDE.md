# PEA Management — Project Instructions

## Parallel subagent safety

- **Shared `/tmp/pea_ohlcv.json` causes silent data corruption** when parallel `pea-price-analyst` agents run — each overwrites the file while others read it. The agent definition now mandates ticker-unique paths (`/tmp/pea_ohlcv_AI.PA.json`). Never revert to a shared path.
- The `compute_indicators.py` script supports `-i <path>` for arbitrary input files. 6mo of daily data (~127 bars) is insufficient for SMA200 — agents should extend to 1y (255 bars) when SMA200 is needed.
