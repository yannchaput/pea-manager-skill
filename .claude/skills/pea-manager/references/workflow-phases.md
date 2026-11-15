# Workflow Phase Details

This file contains the detailed step-by-step procedures for each phase. The SKILL.md quick reference covers routing and key decisions; consult this file when executing a phase.

## Phase 1: First-Time Setup

Triggered when no `TRACKER.md` exists at the project root.

1. **Explain the purpose**: Briefly tell the user this skill tracks and analyzes a PEA portfolio
2. **Ask for account-level information**:
   - Available cash (uninvested euros inside the PEA envelope)
   - PEA opening date. Ask: *"Quand avez-vous ouvert votre PEA ?"*
   - Compute PEA age: *"Votre PEA a [X] ans — en cas de retrait, le gain net du plan [ne supporte que les prélèvements sociaux de 18,6 % / est soumis au PFU de 31,4 % et le plan est clôturé]. Vendre un titre sans sortir l'argent du PEA n'est pas imposé."*
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

**First, filter out positions listed in `## Exceptions` and positions whose Ticker is `—`** (no price series; ask the user for the latest value) — these positions are skipped entirely. No agent is dispatched, no price is fetched, no P&L is computed for them.

For the remaining N positions, dispatch N `pea-price-analyst` agents. Each agent fetches current price, fetches OHLCV data, computes all technical indicators, and returns structured results per the agent's output schema.

**Dispatch recipe** (one call per non-exception position):

```
Agent(subagent_type="pea-price-analyst", prompt="Analyze {NAME} ({TICKER from the Ticker column}, ISIN: {ISIN}) for PEA portfolio review. Position: {SHARES} shares, PRU {PRU}€, strategy: {STRATEGY}. PEA age: {PEA_YEARS} years (opened {PEA_OPENED_DATE}).")
```

**Always pass PEA age as a plain number of years** (e.g. `6.83`, computed from the `PEA opened` date in TRACKER.md), not as qualitative text like ">5 years". The agent forwards this straight to `compute_indicators.py --pea-years`, which derives the tax rate itself — qualitative text has repeatedly gotten reformatted or lost its `>` character in transit (a shell redirection character), silently flipping the tax rate for every position in the review. See `.claude/agents/pea-price-analyst.md` for the exact CLI contract.

The agent definition (`.claude/agents/pea-price-analyst.md`) contains the full procedure, tools, and output schema. Pass all position parameters in the prompt.

**Index check, once per review** (main agent, Bash, alongside the dispatches):

```
python3 .claude/skills/pea-manager/scripts/compute_indicators.py --mode dd --fetch --name "CAC 40" --ticker ^FCHI
```

Keep its `CHANGE: 5d` and `SMA` lines: step 3.3 uses the 5-day change to classify alert breaches.

**Main agent collects all results**, then proceeds to step 3.3 for cross-position synthesis. Exception positions are silently omitted from all synthesis tables and decision outputs — do not mention them unless the user asks.

**Rate limit awareness**: EODHD free plan allows 20 calls/day total across all subagents. Each agent uses `compute_indicators.py --fetch` (free Yahoo chart API, no quota, no temp file) first and only falls back to EODHD when that fails — so Phase 3 rarely touches the EODHD quota. If the limit is near, flag data gaps explicitly.

### Step 3.2: Technical Indicators (computed by pea-price-analyst agent)

The agent returns RSI(14), MACD(12,26,9), Bollinger(20,2σ), SMA 50/200, ATR(14), Volume, and P&L. Full computation procedure, formulas, and output schema: `.claude/agents/pea-price-analyst.md`.

### Step 3.3: Decision by Strategy

The decision rules live in one place: `SKILL.md`, section "3.3 Decision by strategy" (tax context, short and long rules, alert-breach discipline). Apply them from there.

### Step 3.4: Update TRACKER.md

- Update `Last review` date
- Ask user for broker's updated Portfolio market value and Unrealized P&L
- Recompute Capital deployed and Total PEA value
- For each position: append the dated review (price, indicators, verdict) to its section of `HISTORY.md` (create the file or the section if absent), then replace the position's single `Last reviewed` line in the Thesis (or its older `Revue YYYY-MM-DD` line) with one `Last reviewed` line carrying today's date and verdict
- **MANDATORY: Benchmark row.** Append to the `## Benchmark` table in `HISTORY.md`: date, Total PEA value, net deposits or withdrawals since the last row (ask the user), MSCI World ETF price (`fetch_ohlcv.py -t WPEA.PA -r 5d`). Comparing the two columns over time shows whether the active book beats simply holding the ETF.
- **MANDATORY: Read `WATCHLIST.md` and review ALL candidates** (both `## Watchlist — Candidats court terme` and `## Watchlist — Candidats long terme`). Replace each candidate's `Décision` line; the previous one goes to `HISTORY.md`. For each candidate:
  - **Short-term**: re-evaluate every LL-01 checklist item against current data. Every item met (≥2 confirmations, ATR, R/R ≥ 2, results more than 5 sessions away, news cross-check) → ✅ ENTRÉE. ≥2 confirmations with any other item still open → 🟡 TRÈS PROCHE, naming the open item. If thesis broken → 🔴 REFUSÉE.
  - **Long-term**: re-evaluate thesis, valuation, and entry strategy vs current price. Update Décision status.
  - **If ENTRÉE**: tell user and offer to proceed to Phase 2 (update) → Portfolio Composition.
  - **Stale cleanup**: WATCH > 2 months (short-term) or > 3 months (long-term) without trigger → propose removal or thesis refresh.

## Phase 4: New Opportunities

**Do NOT use yfinance screeners/search for Phase 4 discovery.** Yahoo's `yfinance_screen`, `yfinance_get_top`, `yfinance_search` are US-centric — they return zero or near-zero European-domiciled results. Use `scripts/scan_universe.py` + Playwright for discovery. **For candidate price/OHLCV enrichment, `scripts/fetch_ohlcv.py` (Yahoo chart API) is allowed** — it's free, no quota, and returns clean JSON.

### Step 4.0: Strategy Routing (MANDATORY)

**If the user has not specified whether they want short-term or long-term opportunities, ASK before dispatching any agents:**

> *"Quel type d'opportunités recherchez-vous ?"*
> - **Court terme (short)** — trading swing, semaines à mois, signaux techniques (momentum, value plays, rotations sectorielles)
> - **Long terme (long)** — buy & hold, années, dividendes croissants, large caps sous-évaluées, croissance stable

**Once the user answers**, branch into the appropriate scan below.

**If the user already specified** (e.g., "Des idées pour du long terme ?" or "Des opportunités court terme ?"), route directly without asking.

### Phase 4-Short: Short-Term Opportunity Scan

**Data budget**: 0 EODHD calls. Discovery is `scripts/scan_universe.py` (Yahoo chart API, no quota); market-research uses Playwright.

#### Step 4-Short.1: Parallel Scan Dispatch

**Run the script and dispatch one agent concurrently.** Each agent's full procedure, tools, and output format is defined in its own file under `.claude/agents/`. The dispatch prompts below are minimal — the agent definition file is the ground truth for what each agent does.

**Step A — `scan_universe.py`** (replaces the EODHD exchange browse, which could not parse whole-exchange listings and has no market-cap filter; 2026-11-10 post-mortem):

```
python3 .claude/skills/pea-manager/scripts/scan_universe.py --bucket mid --top 25
```

**Step B — pea-french-market-research** (`.claude/agents/pea-french-market-research.md`):

```
Agent(subagent_type="pea-french-market-research", prompt="Research current French market themes, sector rotations, and analyst rating changes via Boursier.com. Return stocks mentioned positively with context, sector themes, and key takeaways.")
```

**Main agent collects all results**, then proceeds to Step 4-Short.2 for merging, filtering, and ranking.

#### Step 4-Short.2: Filters

**First, merge and deduplicate** the script's list and the research agent's list. Normalize ticker formats (`.PA` vs `.DE` etc.) and remove duplicates by ticker or company name.

**Then apply filters** in order:
1. **PEA eligibility**: verify domicile via ISIN country code (first 2 chars). Cross-check with [`references/pea-eligibility.md`](references/pea-eligibility.md).
2. **Preference for small/mid caps**: the `mid` bucket of `assets/universe.json` (an index-membership proxy, not a live market cap)
3. **Diversification**: avoid sector over-concentration vs existing portfolio. Prioritize absent/underweight sectors. **Exclude positions in `## Exceptions` from the sector concentration check** — they do not count toward existing allocation.
4. **Momentum signals**: positive price trend, pullback to key MA, high relative volume, analyst upgrades, upcoming catalyst (earnings, product launch)
5. **Cross-source confirmation**: candidates found by both the script and the Boursier.com research get higher confidence

#### Step 4-Short.3: Present

For each candidate: name, ISIN, sector, market cap, current price, 1-3M performance trend, catalyst/risks, suggested strategy (short), entry price, profit target. Rank by attractiveness in a table.

#### Step 4-Short.4: Register in Watchlist (AUTOMATIC)

Register candidates in `## Watchlist — Candidats court terme` in `WATCHLIST.md`. Follow the same LL-01 checklist procedure as before. Full template: [`references/tracker-template.md`](tracker-template.md).

---

### Phase 4-Long: Long-Term Opportunity Scan

**Data budget**: 0 EODHD calls. Discovery is `scripts/scan_universe.py`; enrich survivors' valuation/dividends with `yfinance_get_ticker_info`.

#### Step 4-Long.1: Parallel Scan Dispatch

**Run the script and dispatch one agent concurrently.**

**Step A — `scan_universe.py`** (replaces the EODHD exchange browse, which could not parse whole-exchange listings and has no market-cap filter; 2026-11-10 post-mortem):

```
python3 .claude/skills/pea-manager/scripts/scan_universe.py --bucket large --top 25
```

**Step B — pea-french-market-research** (`.claude/agents/pea-french-market-research.md`):

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

Register candidates in `## Watchlist — Candidats long terme` in `WATCHLIST.md`. Use the long-term watchlist template from [`references/tracker-template.md`](tracker-template.md).

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

The DD agent returns a `DUE DILIGENCE:` block with support/resistance, trend analysis, R/R ratio, and automated LL-01 scoring. The main agent combines this with the news cross-check (two `pea-news-check` agents, sources `tradingview` and `investir`) to make the final buy/skip decision.

**Key differences from `pea-price-analyst`:**
- No P&L or tax computation (no position yet)
- Adds support/resistance zones, trend structure, R/R ratio
- Automates the 4 LL-01 technical confirmations + ATR check
- Returns `ENTER` / `WATCH` / `SKIP` recommendation

### Cross-Phase Integration (Both Strategies)

- **Phase 3 (next review)**: the main agent MUST check all watchlist candidates from both sections. For short-term candidates: re-evaluate LL-01 criteria. For long-term candidates: re-evaluate thesis and valuation.
- **Phase 4 (new scan)**: cross-check new candidates against existing watchlists to avoid duplicates.
