# Workflow Phase Details

This file contains the detailed step-by-step procedures for each phase. The SKILL.md quick reference covers routing and key decisions; consult this file when executing a phase.

## Phase 1: First-Time Setup

Triggered when no `TRACKER.md` exists in the skill directory.

1. **Explain the purpose**: Briefly tell the user this skill tracks and analyzes a PEA portfolio
2. **Ask for account-level information**:
   - Available cash (uninvested euros inside the PEA envelope)
   - PEA opening date. Ask: *"Quand avez-vous ouvert votre PEA ?"*
   - Compute PEA age: *"Votre PEA a [X] ans — les plus-values sont [exonérées d'impôt / encore soumises au PFU de 31,4%]"*
3. **Ask for portfolio composition**: For each holding — company name, ISIN (or ticker), number of shares, PRU (€), strategy (`short` or `long`)
4. **Compute totals**: Ask for broker's Unrealized P&L and Portfolio market value. Derive Capital Deployed = Portfolio Market Value − Unrealized P&L. Total PEA Value = Available Cash + Portfolio Market Value.
5. **Present full TRACKER.md** — Account Information table + Portfolio Composition table — for user confirmation
6. **Create TRACKER.md** with confirmed data
7. **Proceed to Phase 3** (analysis)

**ISIN lookup**: If unknown, use `mcp__yfmcp__yfinance_search` first, then `mcp__eodhd-mcp__resolve_ticker` or `mcp__eodhd-mcp__get_stocks_from_search` as fallback.

## Phase 2: Portfolio Update

Triggered when `TRACKER.md` exists and user wants to modify holdings.

1. **Read and display** current `TRACKER.md` — Account Information, then Portfolio Composition
2. **Ask about account-level updates**:
   - Available cash — drifts after every buy/sell
   - PEA > 5 years status — if near the boundary, may have switched
   - Capital deployed — only if positions added/removed outside tracked session
3. **Ask about portfolio updates**: modify existing positions (shares, PRU, strategy), add new ones, remove sold ones
4. **Cash adjustments**: selling → add proceeds to cash. buying → deduct cost + estimated fees from cash
5. **PRU changes**: compute weighted average for additional purchases (see formula in tracker-template.md)
6. **Present updated TRACKER.md** for confirmation
7. **Update Thesis** section if strategies or positions changed
8. **Proceed to Phase 3** (analysis)

## Phase 3: Portfolio Analysis

Core analysis phase. Run after setup, after updates, or on user request.

**Execution pattern**: Dispatch one `pea-price-analyst` agent per position for steps 3.1+3.2 combined. Agents run concurrently — each is independent. The main agent collects all results, then runs steps 3.3 (decisions) and 3.4 (TRACKER.md update) sequentially — these need cross-position context.

**Single position** → run steps 3.1+3.2 inline in the main agent (no subagent overhead needed).

### Step 3.1+3.2: Per-Position Agent Dispatch

**First, filter out positions listed in `## Exceptions`** — these positions are skipped entirely. No agent is dispatched, no price is fetched, no P&L is computed for them.

For the remaining N positions, dispatch N `pea-price-analyst` agents. Each agent fetches current price, fetches OHLCV data, computes all technical indicators, and returns structured results per the agent's output schema.

**Dispatch recipe** (one call per non-exception position):

```
Agent(subagent_type="pea-price-analyst", prompt="Analyze {NAME} ({TICKER}, ISIN: {ISIN}) for PEA portfolio review. Position: {SHARES} shares, PRU {PRU}€, strategy: {STRATEGY}. PEA age: {PEA_YEARS} years (opened {PEA_OPENED_DATE}).")
```

**Always pass PEA age as a plain number of years** (e.g. `6.83`, computed from the `PEA opened` date in TRACKER.md), not as qualitative text like ">5 years". The agent forwards this straight to `compute_indicators.py --pea-years`, which derives the tax rate itself — qualitative text has repeatedly gotten reformatted or lost its `>` character in transit (a shell redirection character), silently flipping the tax rate for every position in the review. See `.claude/agents/pea-price-analyst.md` for the exact CLI contract.

The agent definition (`.claude/agents/pea-price-analyst.md`) contains the full procedure, tools, and output schema. Pass all position parameters in the prompt.

**Main agent collects all results**, then proceeds to step 3.3 for cross-position synthesis. Exception positions are silently omitted from all synthesis tables and decision outputs — do not mention them unless the user asks.

**Rate limit awareness**: EODHD free plan allows 20 calls/day total across all subagents. Each agent uses `fetch_ohlcv.py` (free Yahoo chart API, no quota) first and only falls back to EODHD when that fails — so Phase 3 rarely touches the EODHD quota. If the limit is near, flag data gaps explicitly.

### Step 3.2: Technical Indicators (computed by pea-price-analyst agent)

The agent returns RSI(14), MACD(12,26,9), Bollinger(20,2σ), SMA 50/200, ATR(14), Volume, and P&L. Full computation procedure, formulas, and output schema: `.claude/agents/pea-price-analyst.md`.

### Step 3.3: Decision by Strategy

**Tax context check** (before every sell recommendation):
- **PEA < 5 years**: 31.4% PFU. Compute net: *"Gain brut: +X€. Après PFU (31,4%): +Y€ net."*
- **PEA ≥ 5 years**: only 18.6% social charges. *"Gain brut: +X€. PS (18,6%): Y€. Net: +Z€."*
- Never let tax override a price alert, but use PEA age to calibrate recommendations

**Short strategy:**
- Profit target met (default +10-15%) → **SELL**, show gross/net
- RSI > 70 AND near upper Bollinger → strong sell signal
- RSI < 30 AND near lower Bollinger → hold for recovery (unless fundamentals broken)
- MACD bearish crossover → tighten the stop/alert level
- Output: **SELL NOW** / **CONSIDER SELLING** / **HOLD** / **ACCUMULATE** with tax-adjusted return

**Long strategy:**
- Focus on trend, not short-term noise
- Price below PRU → evaluate if thesis still holds
- RSI < 30 → potential buying opportunity to average down
- RSI > 80 → flag even for long holds
- Fundamental deterioration → propose exit strategy (gradual: sell in thirds; immediate: only if thesis broken)
- PEA < 5 years → lean toward holding (tax benefit of waiting is significant)
- Update Thesis section with new observations

**Alert-breach discipline** (LL-03, [`references/lessons-learned.md`](lessons-learned.md)): this covers positions protected only by an alert; a position with a Fortuneo stop (*ordre à seuil de déclenchement*) placed exits automatically and the review just reports the execution. A price alert breach is normally a hard sell trigger (LL-02) — but only for a single, idiosyncratic breach. If ≥3 uncorrelated positions across different sectors breach simultaneously with no shared company-specific news, it's a market-wide pullback, not a portfolio-wide sell signal. Report every breach clearly and keep the alert active, but do not escalate the framing to "action required" — name the pattern to the user and defer to their read of macro conditions.

### Step 3.4: Update TRACKER.md

- Update `Last review` date
- Ask user for broker's updated Portfolio market value and Unrealized P&L
- Recompute Capital deployed and Total PEA value
- Update each position's `Last reviewed` date in Thesis
- Add brief analysis note with date and key findings
- **MANDATORY: Review ALL watchlist candidates** (both `## Watchlist — Candidats court terme` and `## Watchlist — Candidats long terme`). For each candidate:
  - **Short-term**: re-evaluate every LL-01 checklist item against current data. If ≥2 confirmations now met → flag as 🟡 TRÈS PROCHE or ✅ ENTRÉE. If thesis broken → 🔴 REFUSÉE.
  - **Long-term**: re-evaluate thesis, valuation, and entry strategy vs current price. Update Décision status.
  - **If ENTRÉE**: tell user and offer to proceed to Phase 2 (update) → Portfolio Composition.
  - **Stale cleanup**: WATCH > 2 months (short-term) or > 3 months (long-term) without trigger → propose removal or thesis refresh.

## Phase 4: New Opportunities

**Do NOT use yfinance screeners/search for Phase 4 discovery.** Yahoo's `yfinance_screen`, `yfinance_get_top`, `yfinance_search` are US-centric — they return zero or near-zero European-domiciled results. Use EODHD + Playwright for discovery. **For candidate price/OHLCV enrichment, `scripts/fetch_ohlcv.py` (Yahoo chart API) is allowed** — it's free, no quota, and returns clean JSON.

### Step 4.0: Strategy Routing (MANDATORY)

**If the user has not specified whether they want short-term or long-term opportunities, ASK before dispatching any agents:**

> *"Quel type d'opportunités recherchez-vous ?"*
> - **Court terme (short)** — trading swing, semaines à mois, signaux techniques (momentum, value plays, rotations sectorielles)
> - **Long terme (long)** — buy & hold, années, dividendes croissants, large caps sous-évaluées, croissance stable

**Once the user answers**, branch into the appropriate scan below.

**If the user already specified** (e.g., "Des idées pour du long terme ?" or "Des opportunités court terme ?"), route directly without asking.

### Phase 4-Short: Short-Term Opportunity Scan

**EODHD call budget**: ~8-10 calls (exchange-browser only; market-research uses Playwright). If the price batch hits 402 (quota exhausted), enrich candidate prices via `scripts/fetch_ohlcv.py` (free Yahoo chart API) instead.

#### Step 4-Short.1: Parallel Scan Dispatch

**Dispatch two subagents concurrently.** Each agent's full procedure, tools, and output format is defined in its own file under `.claude/agents/`. The dispatch prompts below are minimal — the agent definition file is the ground truth for what each agent does.

**Agent A — pea-eodhd-exchange-browser** (`.claude/agents/pea-eodhd-exchange-browser.md`):

```
Agent(subagent_type="pea-eodhd-exchange-browser", prompt="Scan European exchanges (Euronext Paris, Xetra, Amsterdam, Milan, Madrid) for PEA-eligible mid-cap opportunities. Exclude tickers already in portfolio (read TRACKER.md). Return up to 20 candidates.")
```

**Agent B — pea-french-market-research** (`.claude/agents/pea-french-market-research.md`):

```
Agent(subagent_type="pea-french-market-research", prompt="Research current French market themes, sector rotations, and analyst rating changes via Boursier.com. Return stocks mentioned positively with context, sector themes, and key takeaways.")
```

**Main agent collects all results**, then proceeds to Step 4-Short.2 for merging, filtering, and ranking.

#### Step 4-Short.2: Filters

**First, merge and deduplicate** all candidate lists from Agents A and B. Normalize ticker formats (`.PA` vs `.DE` etc.) and remove duplicates by ticker or company name.

**Then apply filters** in order:
1. **PEA eligibility**: verify domicile via ISIN country code (first 2 chars). Cross-check with [`references/pea-eligibility.md`](references/pea-eligibility.md).
2. **Preference for small/mid caps**: €500M–€10B market cap
3. **Diversification**: avoid sector over-concentration vs existing portfolio. Prioritize absent/underweight sectors. **Exclude positions in `## Exceptions` from the sector concentration check** — they do not count toward existing allocation.
4. **Momentum signals**: positive price trend, pullback to key MA, high relative volume, analyst upgrades, upcoming catalyst (earnings, product launch)
5. **Cross-source confirmation**: candidates found by ≥2 agents get higher confidence

#### Step 4-Short.3: Present

For each candidate: name, ISIN, sector, market cap, current price, 1-3M performance trend, catalyst/risks, suggested strategy (short), entry price, profit target. Rank by attractiveness in a table. Ask user before adding to TRACKER.md.

#### Step 4-Short.4: Register in Watchlist (AUTOMATIC)

Register candidates in `## Watchlist — Candidats court terme` in TRACKER.md. Follow the same LL-01 checklist procedure as before. Full template: [`references/tracker-template.md`](tracker-template.md).

---

### Phase 4-Long: Long-Term Opportunity Scan

**EODHD call budget**: ~8-10 calls (exchange-browser only; market-research uses Playwright). Enrich candidate valuation/dividends via free sources — `scripts/fetch_ohlcv.py` (Yahoo chart) or `yfinance_get_ticker_info` (fundamentals).

#### Step 4-Long.1: Parallel Scan Dispatch

**Dispatch two subagents concurrently.**

**Agent A — pea-eodhd-exchange-browser** (`.claude/agents/pea-eodhd-exchange-browser.md`):

```
Agent(subagent_type="pea-eodhd-exchange-browser", prompt="Scan European exchanges (Euronext Paris, Xetra, Amsterdam, Milan, Madrid) for PEA-eligible LARGE-CAP opportunities (€10B+). Focus on established companies with durable competitive advantages. Exclude tickers already in portfolio (read TRACKER.md). Return up to 15 candidates.")
```

**Agent B — pea-french-market-research** (`.claude/agents/pea-french-market-research.md`):

```
Agent(subagent_type="pea-french-market-research", prompt="Research current French market themes, sector rotations, and analyst rating changes via Boursier.com. Focus on long-term structural themes (energy transition, AI, aging demographics, reshoring). Return stocks mentioned positively with context, sector themes, and key takeaways.")
```

**Main agent collects all results**, then proceeds to Step 4-Long.2.

#### Step 4-Long.2: Filters

**First, merge and deduplicate** candidate lists. Normalize ticker formats and remove duplicates.

**Then apply long-term-specific filters** in order:
1. **PEA eligibility**: verify domicile via ISIN (first 2 chars)
2. **Large cap only**: €10B+ market cap — stability, liquidity, analyst coverage
3. **Durable competitive advantage**: assess moat (brand, network effects, pricing power, patents, regulatory barriers). Exclude commoditized businesses without clear differentiation
4. **Dividend consistency**: preference for ≥3 years of maintained or growing dividends. Flag recent cuts for investigation
5. **Reasonable valuation**: P/E < 25 or P/B < 3 unless exceptional growth justifies premium. Avoid euphoric valuations (P/E > 40)
6. **Diversification**: avoid sector over-concentration vs existing long positions. **Exclude positions in `## Exceptions` from the sector concentration check.**
7. **Cross-source confirmation**: candidates found by ≥2 sources get higher confidence

#### Step 4-Long.3: Present

For each candidate: name, ISIN, sector, market cap, current price, dividend yield + growth history, revenue/earnings growth trend, valuation vs sector peers, moat assessment, key risks. Present in a table ranked by conviction (strongest compounder first). For each, explicitly state: *"Why hold this for 5+ years?"*

#### Step 4-Long.4: Register in Watchlist (AUTOMATIC)

Register candidates in `## Watchlist — Candidats long terme` in TRACKER.md. Use the long-term watchlist template from [`references/tracker-template.md`](tracker-template.md).

Each long-term watchlist entry includes:
- Date spotted, current price
- Long-term thesis (moat, growth drivers, dividend trajectory)
- Consensus analyst rating + target
- Valuation metrics (P/E, P/B, dividend yield vs sector)
- Key risks (competitive, regulatory, macro)
- Entry strategy (lump sum vs thirds vs limit order below current price)
- Allocation target

---

### Pre-Entry Technical DD (Phase 4)

When the main agent needs technical due diligence on a candidate before entry, dispatch `pea-dd-analyst` instead of `pea-price-analyst`:

```
Agent(subagent_type="pea-dd-analyst", prompt="Due diligence on {TICKER} for PEA {short/long} entry. Entry ~{€X}, target {€Y}, stop {€Z}.")
```

The DD agent returns a `DUE DILIGENCE:` block with support/resistance, trend analysis, R/R ratio, and automated LL-01 scoring. The main agent combines this with news cross-check (TradingView + Investir) to make the final buy/skip decision.

**Key differences from `pea-price-analyst`:**
- No P&L or tax computation (no position yet)
- Adds support/resistance zones, trend structure, R/R ratio
- Automates the 4 LL-01 technical confirmations + ATR check
- Returns `ENTER` / `WATCH` / `SKIP` recommendation

### Cross-Phase Integration (Both Strategies)

- **Phase 3 (next review)**: the main agent MUST check all watchlist candidates from both sections. For short-term candidates: re-evaluate LL-01 criteria. For long-term candidates: re-evaluate thesis and valuation.
- **Phase 4 (new scan)**: cross-check new candidates against existing watchlists to avoid duplicates.
- **Budget conflicts**: if both short and long scans are requested in the same session, run them sequentially (short first, then long) to stay within the 20-call daily EODHD limit. If the budget is already partially consumed, run only the requested scan type.
