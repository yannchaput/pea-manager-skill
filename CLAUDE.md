# PEA Management — Project Instructions

## Scope: skill repo, not a code project

This repo is dedicated to the `pea-manager` skill (`.claude/skills/pea-manager/`), its agents and `TRACKER.md`. It is not a software project, so these global code-writing rules **do not apply here**:

- No code-writing skills or commands: no `ponytail` (`/ponytail:*`, including the pre-commit review), no `/simplify`, no `code-simplifier`, no `superpowers:test-driven-development`.
- No code quality gate: no `ruff`, no `uv run pytest` (or `pytest --cov`), no `interrogate`, no `uv run` at all.
- Commit directly when asked; there is no review or gate step before a commit.

## Parallel subagent safety

- **Shared `/tmp/pea_ohlcv.json` causes silent data corruption** when parallel `pea-price-analyst` agents run — each overwrites the file while others read it. The agent definition now mandates ticker-unique paths (`/tmp/pea_ohlcv_AI.PA.json`). Never revert to a shared path.
- The `compute_indicators.py` script supports `-i <path>` for arbitrary input files. 6mo of daily data (~127 bars) is insufficient for SMA200 — agents should extend to 1y (255 bars) when SMA200 is needed.
- **PEA age must be passed to `compute_indicators.py` as a plain number of years (`--pea-years 6.83`), never as qualitative text like `">5 years"`.** The old `--pea-age` string-matching logic silently fell back to the 30% PFU tax rate for every position when a parallel `pea-price-analyst` agent reformatted the free text and dropped the `>` in transit (it's also a shell redirection character, an extra footgun if ever unquoted) — every net P&L in a Phase 3 review was wrong with no error raised. `--pea-age` still exists but is cosmetic-only now (display label); it has zero effect on the tax rate. If the dispatch prompt only states a qualitative age, convert it to a number before dispatching.
