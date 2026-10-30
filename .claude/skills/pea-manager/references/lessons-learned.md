# Lessons Learned

## LL-01: Never Buy a Falling Knife Without Confirmation (Alten, June 2026)

### What Happened

Recommended buying Alten at 62.73 € after a −25% pullback from ATH, citing attractive valuation and analyst consensus. Four days later the stock dropped to 57.10 € (−9%). The user sold at a loss of −176.40 €.

### Root Causes

1. **Confirmation bias**: Interpreted the −25% drop as an opportunity without investigating *why* it was falling
2. **No technical confirmation before entry**: Entered before any bullish reversal signal (no MACD crossover, no RSI recovery, no volume surge)
3. **Over-reliance on analyst consensus**: "Strong Buy" ratings and 12-month targets say nothing about entry timing
4. **Volatility underestimated**: Stop loss set without checking ATR; position moved −9% in 4 days

### The News Narrative (Hidden from English-Only APIs)

**TradingView** (English, Reuters/Quartr):
- Net income −42.6% in FY 2025
- Organic growth guidance: 0% to −0.5% for H1 2026
- CEO replaced in October 2025
- Automotive sector −15%
- Legal risks flagged

**Investir Les Echos** (French, AFP/Agefi/Reuters):
- Apr 28: "Alten vise une croissance organique entre 0% et -0.5% en 2026" (AFP)
- Mar 12: "Alten : du retard au rallumage" (Conseil de la rédaction)
- Mar 4: "Alten sortira de l'indice Stoxx Europe 600 le 23 mars" (Agefi-Dow Jones)
- Feb 24: "Alten — Baisse de 42.6% du résultat net en 2025" (Reuters)
- Sep 2025: "Alten nomme Cyril Malargé (ex-Sopra Steria) au poste de DG"

→ Five negative signals across 6+ months. This was a structural decline, not a technical pullback. The low P/E was a value trap.

### Corrective Rules (Now Mandatory for All Short Entries)

These rules are codified in SKILL.md as the mandatory entry checklist. They include:

1. **Require ≥2 technical confirmations** before entry (RSI >30 crossover, MACD bullish crossover, green candle with volume >1.5× avg, price >5-day EMA)
2. **Diagnose the drop** — check both TradingView AND Investir for profit warnings, guidance cuts, management departures
3. **Check ATR** before setting price alert level (≥1.5× ATR; if >10% of entry → reduce size or skip)
4. **Scale in** — ⅓ at first confirmation, ⅓ after support holds 3+ days, ⅓ on breakout above key MA
5. **News as contrary signal** — mandatory TradingView + Investir checks before finalizing any buy recommendation

## LL-02: Never Enter a Downtrend on a Statistical Pattern Without Confirmation (GTT, June–July 2026)

### What Happened

Entered GTT at ~196.57 € on June 17, 2026 (ex-dividend date), expecting a "post-dividend rebound" pattern. The stock had been in a 6-week downtrend from its May 5 peak of 206.74 €. Instead of rebounding, the stock continued falling — reaching an intraday low of 176.80 € on June 26 (−11.2% in 7 sessions). The stop loss at 180 € was breached intraday but not executed. The stock subsequently recovered to ~189.70 €, but the thesis had already failed: the post-dividend rebound never materialized because the pre-dividend decline (−6.1%) had already more than priced in the 4.94 € dividend.

### Root Causes

1. **Entry into an established downtrend**: The stock made 6 consecutive lower highs from May 5 to June 16. MACD was negative since May 27 (3 weeks before entry). EMA12 < EMA26 throughout. RSI was neutral-low (~45), not oversold.
2. **"Rebond post-dividende" was a statistical mirage**: The stock opened at 195.40 € on ex-div date — 6.18 € ABOVE the theoretical ex-dividend price (194.16 − 4.94 = 189.22 €). The market had already absorbed the dividend. There was no "gap" to fill, therefore no "rebound" to expect.
3. **Dividend math error**: The pre-dividend decline (−12.74 € from the May 5 peak) exceeded the dividend amount (4.94 €) by 2.6×. The excess decline (−7.80 €, or −3.8% beyond dividend effect) was real selling pressure, not dividend mechanics. This was a continuation signal, not a buying opportunity.
4. **No catalyst within 6 weeks**: The next meaningful event (H1 2026 results) was July 28 — 6 weeks away. There was no reason for the stock to reverse in the short term.
5. **Stop loss not executed**: The 180 € stop was breached intraday on June 26 (low: 176.80 €). The position survived only by luck — the subsequent recovery to 189.70 € was not predictable.

### Technical Snapshot at Entry (June 16–17, 2026)

| Indicator | Value | Signal |
|-----------|-------|--------|
| MACD | −0.83 | ❌ Bearish (negative for 3 weeks) |
| MACD Signal | −1.00 | ❌ Below MACD line |
| MACD Histogram | +0.17 | 🟡 Marginally positive (divergence, not crossover) |
| RSI(14) | 45.1 | 🟡 Neutral — not oversold, no reversal signal |
| EMA12 vs EMA26 | 196.31 < 197.14 | ❌ Bearish alignment |
| Price vs EMA12 | 194.16 < 196.31 | ❌ Below short-term average |
| Trend structure | 6 lower highs since May 5 | ❌ Established downtrend |
| Pre-div decline vs dividend | −12.74 € vs 4.94 € div | ❌ Selling pressure 2.6× dividend |

**Verdict: 4 ❌, 2 🟡, 0 ✅. No justification for entry.**

### The Parallel with Alten (LL-01)

| | Alten (LL-01) | GTT (LL-02) |
|---|---|---|
| Pre-entry decline | −25% | −6.1% |
| Entry thesis | "Valorisation attractive" | "Rebond post-dividende" |
| Trend at entry | Bearish for months | Bearish for 6 weeks |
| Technical confirmation | None | None |
| MACD at entry | Bearish | Bearish |
| RSI at entry | Oversold (~25) — at least a case could be made | Neutral (~45) — worse, no reversal signal at all |
| Short-term catalyst | None | None (H1 results 6 weeks away) |
| Outcome | −9.3% in 4 days | −11.2% in 7 days |
| Stop loss execution | Executed by user at −9.3% | NOT executed — survived by luck |

**Common thread**: Fundamentally sound companies (high margins, reasonable valuations) entered during downtrends without technical confirmation. Valuation does not protect against momentum.

### Corrective Rules (Now Mandatory)

These rules extend the LL-01 checklist. They apply specifically to **dividend-capture and post-dividend rebound strategies**:

1. **Verify the dividend was actually the cause of the decline.** Compute: `pre-div decline (€) ÷ dividend amount (€)`. If ratio > 1.5× → the decline is NOT just the dividend. Something else is driving selling. Do not enter.
2. **Check the ex-dividend open vs. theoretical price.** If the stock opens ABOVE the theoretical ex-dividend price (close − dividend) → the market has already repriced. The rebound already happened. Do not enter.
3. **Require 3 confirmations for any entry into a downtrend** (stricter than LL-01's 2):
   - [ ] MACD bullish crossover (line crossing above signal, not just histogram turning positive)
   - [ ] Price closes above EMA12
   - [ ] RSI > 50 (momentum has shifted from bearish to bullish territory)
4. **Price alert = mandatory sell, not a suggestion; better, place a stop.** Fortuneo does offer trigger orders (*ordre à seuil de déclenchement*, *à plage de déclenchement*), so a stop at the alert level removes the dependence on acting by hand (a stop still sells at market on a gap). Where only an alert exists, when it is breached the user must sell at the next market session — the recovery might not come next time. The GTT stop breach on June 26 was survived only by luck (rebound from 176.80 € to 189.70 €). Next time the stock may not recover. Tag breached positions as 🔴 CRITICAL and remind the user explicitly: *"L'alerte à X € a été franchie. Vous devez vendre au prochain marché."*
5. **No entry without a catalyst within 2 weeks.** "H1 results in 6 weeks" is not a catalyst. Earnings, product launches, contract wins, analyst days — something concrete and imminent.

### Red Flags — Cancel the Entry If You See These

- [ ] "The dividend will cause a rebound" → Check ratio. If pre-div drop > 1.5× dividend, this is false.
- [ ] "It's a quality company at a good price" → Quality companies fall further in downtrends. Wait for confirmation.
- [ ] "RSI is neutral, not overbought, so it can go up" → Neutral RSI in a downtrend means the trend can continue. It's not a signal.
- [ ] "MACD histogram is turning positive" → Histogram divergence is NOT a crossover. Wait for the actual crossover.
- [ ] "The stop loss will protect me" → Only if it is actually placed (*ordre à seuil de déclenchement*) and still valid; stops expire and gap through. A price alert alone works only if you act on it immediately when breached.

## LL-03: Don't Force Sell Decisions on Market-Wide Alert Breaches (September 2026)

### What Happened

During a Phase 3 review on Sept 9, 2026, four unrelated positions (Arkema short, Vinci long, Sanofi short, Saint-Gobain long) hit or breached their price-alert levels simultaneously. Following the LL-02 rule that "a price alert is a hard sell trigger, not a suggestion," the agent flagged all four as 🔴 CRITICAL WATCH and pushed toward immediate sell decisions. The user rejected this: *"Pas de panique. On est sur un marché bearish, on ne prend pas de décisions."* The breaches were a broad market-wide pullback, not idiosyncratic weakness in any of the four names.

### Root Cause

LL-02's "hard trigger" rule was written for a **single-position** breach (GTT), where the breach reflects stock-specific information (failed thesis, momentum shift). It does not distinguish that case from **multiple simultaneous breaches across uncorrelated positions/sectors**, which is evidence of a market-level move, not a signal about any one company. Applying the single-position rule mechanically at the portfolio level manufactures a panic-sell recommendation the underlying evidence doesn't support.

### Corrective Rule (Qualifies LL-02, Does Not Replace It)

1. **Single-position, idiosyncratic breach** (alert-only position) → LL-02 still applies in full: treat the price alert as a hard trigger, tag 🔴 CRITICAL WATCH, tell the user to sell at the next session.
2. **Multiple simultaneous breaches across uncorrelated positions/sectors, with no idiosyncratic news on any of them** → treat as a market-wide signal, not a portfolio-wide sell trigger:
   - Report every breach clearly and keep the alert active for the next review — do not drop or soften the reporting.
   - Do NOT frame it as requiring an immediate decision or escalate the language to "action required."
   - Explicitly name the pattern to the user (e.g. *"4 positions sur des secteurs différents ont franchi leur alerte le même jour — probable mouvement de marché, pas de signal spécifique à chaque titre"*) and defer to the user's read of macro conditions when given.
3. When in doubt whether a breach is idiosyncratic or market-wide, check if ≥3 positions across different sectors breached on the same session — if yes, default to the market-wide framing above.
