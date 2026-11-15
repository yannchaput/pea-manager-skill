# PEA Management — Project Instructions

## Scope: skill repo, not a code project

This repo holds the `pea-manager` skill (`.claude/skills/pea-manager/`), its agents (`.claude/agents/pea-*.md`) and the private state files. These global code-writing rules **do not apply here**:

- No `ponytail` (`/ponytail:*`, including the pre-commit review), no `/simplify`, no `code-simplifier`, no `superpowers:test-driven-development`.
- No quality gate: no `ruff`, no `pytest`, no `interrogate`, no `uv run` at all.
- Commit directly when asked; no review or gate step before a commit.

## Editing the skill

- **Any edit to the skill, its references, evals or agents: load `superpowers:writing-skills` first.**
- Script change: add an assert to `scripts/selfcheck.py`, watch it fail, then fix. `python3 .claude/skills/pea-manager/scripts/selfcheck.py` must print `OK`.
- Decision rules live only in `SKILL.md` section 3.3; do not copy them into `references/`.

## State files (git-ignored, with `docs/`)

- `TRACKER.md` (account, portfolio, thesis), `WATCHLIST.md` (candidates), `HISTORY.md` (append-only: past reviews, sold positions, benchmark).
- Keep each under ~50 KB so one Read returns the whole file; move old material to `HISTORY.md`, never delete it.

## Parallel subagent safety

- Never use a shared `/tmp/pea_ohlcv.json`: parallel agents overwrite it and corrupt each other's data. Use `compute_indicators.py --fetch` (no file, 1y of bars). The EODHD fallback writes a per-ticker path (`/tmp/pea_ohlcv_AI_PA.json`).
- With `-i <path>`, supply 1y of bars; 6mo is too short for SMA200.
- Pass PEA age as a number (`--pea-years 6.83`), never as text like `">5 years"`: reformatted text once silently applied the wrong tax rate to every position. `--pea-age` is a display label only.
