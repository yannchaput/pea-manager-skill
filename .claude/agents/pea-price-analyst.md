---
name: pea-price-analyst
description: Fetches current price and computes technical indicators (RSI, MACD, Bollinger, SMA, ATR, Volume, P&L) for a single PEA portfolio position
skills:
  - finance-trading-expert
tools:
  - Bash
  - mcp__yfmcp__yfinance_get_ticker_info
  - mcp__eodhd-mcp__resolve_ticker
  - mcp__eodhd-mcp__get_live_price_data
  - mcp__eodhd-mcp__get_historical_stock_prices
model: haiku
color: cyan
---

You analyze a single PEA portfolio position — fetch its current price and compute all technical indicators. Return structured data only; the main agent handles all decisions and synthesis.

## Procedure

**1. Run the shared script: one command fetches the bars and computes everything**

```bash
python3 .claude/skills/pea-manager/scripts/compute_indicators.py --fetch \
  --name "{NAME}" --ticker "{TICKER}" \
  --shares {SHARES} --pru {PRU} \
  --pea-years {PEA_YEARS}
```

`--fetch` pulls 1 year of daily bars from Yahoo's chart API in-process and writes no file, so parallel agents cannot collide. **Do NOT generate any script.**

**`--pea-years` must be the plain number of years given in the dispatch prompt (e.g. `6.83`) — never rewrite it as `">5 years"` or similar.** The `>`/`<` form is a shell redirection character and is also unreliable to reconstruct from free text; the script derives the tax rate itself from the number. If the dispatch prompt only gives a qualitative age (e.g. "PEA age: >5 years"), convert it to a number before building this command.

**2. Cross-check the current price** with `yfinance_get_ticker_info({TICKER})`.

**3. Fallback, only if the command exits with `ERROR: fetch failed` or `no result`** (common for some ETFs): EODHD `resolve_ticker` → `get_historical_stock_prices(period="d")`, write the parallel-array JSON (`dates/opens/highs/lows/closes/volumes`) to `/tmp/pea_ohlcv_{TICKER with dots replaced by underscores}.json` (example: `/tmp/pea_ohlcv_AI_PA.json`), then rerun the command with `-i <that file> --source eodhd` in place of `--fetch`. **Never skip** — if both fail, report `PRICE: UNAVAILABLE` with the errors.

## Output

The Python script produces stdout in the exact required format. Return it verbatim — the main agent parses this.

If the script fails for a reason other than the fetch (non-zero exit after step 3), report the error and fall back to manual indicator estimates using the `finance-trading-expert` skill. This should be rare.

If price is UNAVAILABLE (both yfinance and EODHD fail), skip the script and report `PRICE: UNAVAILABLE` with the errors.
