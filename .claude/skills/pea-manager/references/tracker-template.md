# TRACKER.md Format Reference

This is the full template and column specification for the portfolio tracker.

## Full Template

```markdown
# PEA Portfolio Tracker

## Account Information

| Field | Value |
|-------|-------|
| **Capital deployed** | €X,XXX.XX |
| **Available cash** | €X,XXX.XX |
| **Portfolio market value** | €X,XXX.XX |
| **Unrealized P&L** | +€XXX.XX |
| **Total PEA value** | €X,XXX.XX |
| **PEA opened** | YYYY-MM-DD |
| **PEA > 5 years** | Yes/No |
| **Last review** | YYYY-MM-DD |

## Exceptions

Positions listed here are **excluded from Phase 3 and Phase 4 analysis**. They remain in Portfolio Composition for accounting but are skipped during portfolio review and opportunity scans. Use for permanent buy-and-hold core holdings (e.g., passive world ETF) that never require active sell/hold decisions.

| Name | ISIN | Reason |
|------|------|--------|
| Company Name | XX0000000000 | Buy & hold permanent — pas de décision active |

## Portfolio Composition

| Name | ISIN | Nb Shares | PRU (€) | Strategy |
|------|------|-----------|---------|----------|
| Company Name | XX0000000000 | N | XX.XX | long/short |

## Closed Positions

| Name | Shares Sold | Sell Price (€) | PRU (€) | P&L (€) | P&L % |
|------|------------|----------------|---------|---------|-------|
| Company Name | N | XX.XX | XX.XX | ±XXX.XX | ±XX.XX% |
| **Total** | | | | **±XXX.XX** | |

## Thesis

### Company Name (strategy)
- **Date entered**: YYYY-MM-DD
- **Thesis**: One sentence on why this position exists
- **Exit conditions**: Specific, measurable conditions
- **Last reviewed**: YYYY-MM-DD
```

## Account Information Fields

- **Capital deployed**: Total cost basis of current positions. Best obtained from broker (`Portfolio market value − Unrealized P&L`). Can also be computed as ∑ (PRU × Nb Shares) but verify against broker.
- **Available cash**: Uninvested cash inside the PEA envelope. Ask the user — cannot be inferred.
- **Portfolio market value**: Sum of (current price × Nb Shares) across positions, or as reported by broker.
- **Unrealized P&L**: `Portfolio market value − Capital deployed`. Broker figure is most reliable.
- **Total PEA value**: `Available cash + Portfolio market value`
- **PEA opened**: Date the PEA plan was opened — determines the 5-year tax clock.
- **PEA > 5 years**: Derived from opening date. `Yes` → gains tax-free (only 17.2% social charges). `No` → 30% flat tax (PFU).
- **Last review**: Most recent portfolio analysis date. Updated after each Phase 3 run.

## Portfolio Columns

- **Name**: Company name (not just ticker)
- **ISIN**: 12-character International Securities Identification Number — critical for PEA eligibility
- **Nb Shares**: Quantity held
- **PRU (Prix de Revient Unitaire)**: Average cost basis per share in euros — mandatory for P&L calculation
- **Strategy**: `short` (trading, weeks-to-months) or `long` (buy and hold, years)

## PRU Update Formula

When additional shares are purchased at a different price:
```
New PRU = ((Old_Shares × Old_PRU) + (New_Shares × New_Purchase_Price)) / (Old_Shares + New_Shares)
```

## Closed Positions

- **Move fully liquidated positions** from Portfolio Composition to Closed Positions
- **Partial sales**: Record only the sold portion. Update Nb Shares in Portfolio Composition.
- **P&L (€)**: `(Sell Price − PRU) × Shares Sold`
- **P&L %**: `(Sell Price − PRU) / PRU × 100`
- Keep the **Total row** updated

## Watchlist — Candidats court terme

Candidates identified during Phase 4, awaiting technical confirmation before entry. Each candidate has a mini-thesis with LL-01 entry criteria — the next portfolio review MUST re-evaluate each one.

```markdown
## Watchlist — Candidats court terme

Candidats identifiés en Phase 4, en attente de confirmation technique pour entrée.

### Stock Name (TICKER.PA) — ISIN XX0000000000
- **Repérée le**: YYYY-MM-DD
- **Cours actuel**: XX.XX € (−XX.X % depuis le plus haut/sur 52 semaines)
- **Thèse**: 1-2 phrases expliquant pourquoi c'est une opportunité court terme
- **Consensus**: Rating, objectif XX € (+XX %)
- **Point de vigilance**: Risque principal ou point noir à surveiller
- **Catalyseur**: Résultats/événement le YYYY-MM-DD
- **Critères d'entrée LL-01**:
  - [ ] RSI(14) repasse au-dessus de 30 (ou autre seuil pertinent)
  - [ ] MACD bullish crossover
  - [ ] Bougie verte avec volume >1,5× moyenne
  - [ ] Prix repasse au-dessus de la SMA5
- **Alerte**: XX.XX € (1,5× ATR sous le point d'entrée)
- **Allocation cible**: ~XXX € (N actions)
- **Décision**: ⏳ WATCH / 🟡 TRÈS PROCHE / 🔴 REFUSÉE — justification courte
```

### Watchlist Entry Format Rules

- **ISIN is mandatory** — it validates PEA eligibility; first 2 chars must be EU/EEA
- **Critères d'entrée LL-01**: always a checklist of ≥4 items. At minimum: RSI crossing signal, MACD crossover, green candle + volume, price vs SMA5. Adapt thresholds to the specific setup (e.g., "RSI repasse au-dessus de 30" vs "RSI quitte la zone de survente").
- **Alerte**: computed as `entry_price − 1.5× ATR(14)`. Must be explicit. If ATR not yet computed, mark as "À calculer avant entrée".
- **Allocation cible**: absolute € amount + share count. Must fit within available cash.
- **Décision**: one of:
  - ⏳ **WATCH** — waiting for catalyst/confirmation, not yet actionable
  - 🟡 **TRÈS PROCHE** — setup is nearly complete, could enter any day
  - 🔴 **REFUSÉE** — thesis broken or LL-01 failed definitively (keep for audit trail)
  - ✅ **ENTRÉE** — move to Portfolio Composition, remove from watchlist
- **Cleanup rule**: if a candidate has been WATCH for >2 months without triggering, remove it (stale thesis). If REFUSÉE, keep for 1 month then remove.
- **At each Phase 3 review**: the main agent must also re-check all watchlist candidates against their LL-01 criteria. If a candidate triggers entry → move to Phase 2 (update) then Portfolio Composition.

## Watchlist — Candidats long terme

Long-term buy-and-hold candidates identified during Phase 4-Long. These are evaluated on fundamentals, not technical timing. No LL-01 checklist — use a thesis-and-valuation framework instead.

```markdown
## Watchlist — Candidats long terme

Candidats identifiés en Phase 4-Long, en attente d'un point d'entrée favorable ou de conviction supplémentaire.

### Stock Name (TICKER.PA) — ISIN XX0000000000
- **Repérée le**: YYYY-MM-DD
- **Cours actuel**: XX.XX €
- **Thèse long terme**: 2-3 phrases — moat, croissance, dividende, pourquoi détenir 5+ ans
- **Consensus**: Rating, objectif XX € (+XX %)
- **Valorisation**:
  - P/E (trailing): XX.X
  - P/E (forward): XX.X
  - P/B: X.X
  - Dividend yield: X.X% (historique: X ans de croissance)
  - vs secteur: décote / prime de X%
- **Croissance**: Revenue +XX% / Earnings +XX% (3-year CAGR)
- **Risques**: Concurrentiel, réglementaire, macro — les 2-3 principaux
- **Stratégie d'entrée**: ⬜ Lump sum / ⬜ ⅓ tranches / ⬜ Ordre limite sous XX € — justification
- **Allocation cible**: ~XXX € (N actions)
- **Décision**: ⏳ WATCH / 🟡 CONVICTION ÉLEVÉE / 🔴 REFUSÉE — justification courte
```

### Long-Term Watchlist Entry Format Rules

- **ISIN is mandatory** — validates PEA eligibility
- **Thèse long terme**: must answer "Why hold for 5+ years?" — not a trade thesis. Include competitive advantage (moat), growth drivers, and dividend trajectory.
- **Valorisation**: compare to sector peers, not absolute thresholds. A P/E of 22 in Tech may be cheap; a P/E of 22 in Utilities may be expensive.
- **Croissance**: 3-year CAGR preferred over single-year snapshots. If unavailable, note the most recent 2-3 fiscal years.
- **Stratégie d'entrée**: long-term entries don't need LL-01 technical timing. Choose:
  - **Lump sum** — conviction is high, valuation is attractive now, enter at market
  - **⅓ tranches** — want to average in over weeks/months, reduce timing regret
  - **Ordre limite** — specific entry price desired (e.g., below SMA200, after a pullback). Specify the limit price and rationale.
- **Décision**: one of:
  - ⏳ **WATCH** — thesis valid but waiting for better entry price or more research
  - 🟡 **CONVICTION ÉLEVÉE** — ready to enter, just needs user approval
  - 🔴 **REFUSÉE** — thesis broken, overvalued, or better alternatives exist (keep for audit trail)
  - ✅ **ENTRÉE** — move to Portfolio Composition, remove from watchlist
- **Cleanup rule**: if WATCH for >3 months without action, propose removal or thesis refresh. Long-term theses age slower than short-term setups.
- **At each Phase 3 review**: the main agent re-checks valuation and thesis for each long-term candidate. Has the price moved closer to the entry strategy? Has the thesis changed?
