# PEA Manager -- Phase 1: First-Time Setup (Simulated Run)

## Step 1: Purpose Explanation

> Bonjour ! Je vais vous aider a suivre et analyser votre portefeuille PEA. Ce skill permet de :
> - Tenir a jour la composition de votre portefeuille (actions, PRU, strategie)
> - Analyser chaque position avec des indicateurs techniques (RSI, MACD, Bollinger, SMA)
> - Vous donner des recommandations claires : VENDRE, GARDER, ou ACCUMULER
> - Chercher de nouvelles opportunites PEA-eligibles (actions europeennes uniquement)
>
> Pour commencer, j'ai besoin de quelques informations sur vos positions.

## Step 2: Portfolio Composition Received from User

The user provided:

| Field | Position 1 | Position 2 |
|-------|-----------|-----------|
| **Company** | TotalEnergies | STMicroelectronics |
| **Shares** | 50 | 100 |
| **PRU (cost basis)** | 42.50 EUR | 28.75 EUR |
| **Strategy** | long (dividendes, long terme) | short (revente rapide des que ca monte) |

## Step 3: ISIN Lookup (Simulated)

### What I WOULD do with live tools:

I would call `mcp__yfmcp__yfinance_search` with the company names to find the correct tickers and ISINs, then verify PEA eligibility via `mcp__yfmcp__yfinance_get_ticker_info` to check the `country` and `exchange` fields.

### Expected results based on known data:

**TotalEnergies:**
- Ticker: TTE.PA (Euronext Paris)
- ISIN: FR0000120271
- Country: France
- Exchange: EPA (Euronext Paris)
- PEA eligible: YES (France is in EU/EEA, ISIN starts with FR)

**STMicroelectronics:**
- Ticker: STMPA.PA (Euronext Paris)
- ISIN: NL0000226223
- Country: Netherlands (siege social), traded on Euronext Paris
- Exchange: EPA (Euronext Paris)
- PEA eligible: YES (Netherlands is in EU/EEA, ISIN starts with NL, stock is traded on a European exchange)

### Questions I WOULD ask the user before confirming:

1. "Pouvez-vous confirmer ces ISINs ? TotalEnergies = FR0000120271, STMicroelectronics = NL0000226223"
2. "Pour TotalEnergies (strategie long) : quelle est votre these d'investissement ? Pourquoi voulez-vous les garder longtemps ? Avez-vous un prix de sortie ou une condition de vente (ex: baisse du dividende de plus de X%) ?"
3. "Pour STMicroelectronics (strategie short) : quel est votre objectif de gain ? Par exemple +10% (31.63 EUR), +15% (33.06 EUR) ? Et votre stop-loss : -8% (26.45 EUR) ? Sur quel horizon de temps pensez-vous les revendre ?"
4. "A quelle date avez-vous ouvert votre PEA ? (important pour la fiscalite : les gains sont taxes a 30% avant 5 ans, puis exonerations d'impot apres 5 ans)"
5. "Avez-vous achete ces actions en une seule fois ou en plusieurs fois ? Si en plusieurs fois, je dois calculer un PRU pondere."
6. "A quelle date avez-vous achete chaque position ? Cela me permettra de suivre la performance depuis l'entree."

## Step 4: Portfolio Table (for user confirmation)

Before saving, I would present this exact table and ask the user to confirm:

```markdown
# PEA Portfolio Tracker

## Portfolio Composition

| Name | ISIN | Nb Shares | PRU (EUR) | Strategy |
|------|------|-----------|---------|----------|
| TotalEnergies | FR0000120271 | 50 | 42.50 | long |
| STMicroelectronics | NL0000226223 | 100 | 28.75 | short |
```

**Capital investi total :**
- TotalEnergies : 50 x 42.50 EUR = 2 125.00 EUR
- STMicroelectronics : 100 x 28.75 EUR = 2 875.00 EUR
- **Total : 5 000.00 EUR**

## Step 5: Thesis Section (what I would build with user input)

### TotalEnergies (long)
- **Date entered**: [A demander a l'utilisateur -- suppose 2026-06-10]
- **Thesis**: [A demander] -- probablement : Dividende stable et croissant, secteur energetique en transition, societe bien etablie du CAC 40
- **Exit conditions**: [A demander] -- suggestion : baisse du dividende >20% OU deterioration structurelle du secteur energetique
- **Last reviewed**: 2026-06-14

### STMicroelectronics (short)
- **Date entered**: [A demander -- suppose 2026-06-12]
- **Thesis**: Cycle des semi-conducteurs haussier, nouveau cycle de produits, rebound technique
- **Exit target**: +15% gain (target price: 33.06 EUR) [valeur par defaut suggeree]
- **Stop loss**: -8% (26.45 EUR) [valeur par defaut suggeree]
- **Last reviewed**: 2026-06-14

## Step 6: What Phase 3 (Analysis) Would Look Like

If we were proceeding to analysis, here is exactly what I would do:

### 6.1 Fetch Current Prices

I would call:
- `mcp__yfmcp__yfinance_get_price_history(symbol="TTE.PA", period="3mo", interval="1d")` 
- `mcp__yfmcp__yfinance_get_price_history(symbol="STMPA.PA", period="3mo", interval="1d")`
- `mcp__yfmcp__yfinance_get_ticker_info(symbol="TTE.PA")` for current price and metrics
- `mcp__yfmcp__yfinance_get_ticker_info(symbol="STMPA.PA")` for current price and metrics

### 6.2 Technical Analysis (per stock)

I would invoke the **finance-trading-expert** skill via `Skill(skill="finance-trading-expert")` to get access to indicator calculation formulas, then compute:

For each position:
1. **RSI (14-day)**: Identify overbought (>70) / oversold (<30)
2. **MACD (12, 26, 9)**: Detect crossovers
3. **Bollinger Bands (20-day, 2 sigma)**: Check price position vs bands
4. **SMA 50 and SMA 200**: Golden cross / death cross detection
5. **Volume analysis**: Compare recent volume to 20-day average
6. **Current P&L**: (Current Price - PRU) x Nb Shares in EUR and %

### 6.3 Strategy-Based Decisions

**STMicroelectronics (short strategy) -- priority analysis:**
- Calculate exact P&L % from entry
- If price > target (33.06 EUR, +15%): "VENDRE -- objectif atteint, gain de X EUR"
- If RSI > 70 AND price near upper Bollinger Band: "ENVISAGER DE VENDRE -- surachete, prendre le profit"
- If RSI < 30 AND price near lower Bollinger Band: "GARDER -- survente, attendre le rebond"
- If MACD bearish crossover: "ATTENTION -- resserrer le stop-loss"
- If price < stop loss (26.45 EUR, -8%): "VENDRE -- stop-loss atteint, perte limitee a X EUR"
- Clear recommendation with reasoning and confidence level

**TotalEnergies (long strategy):**
- Focus on long-term trend, not daily fluctuations
- Check if price substantially below PRU -- if so, does the dividend thesis still hold?
- If RSI < 30: "Opportunite de renforcement -- potentiellement suracheté, bon prix pour accumuler"
- Verify dividend yield remains attractive vs PRU
- Update thesis notes with current observations
- If fundamental issues detected: propose gradual exit strategy (sell in thirds)

### 6.4 Tax Awareness

I would remind the user:
- Si le PEA a moins de 5 ans, toute vente de STMicroelectronics avec gain sera taxee a 30% (flat tax)
- Apres 5 ans, les gains sont exoneres d'impot (seules les charges sociales de 17.2% s'appliquent)
- Pour TotalEnergies (long), les dividendes percus dans le PEA sont reinvestissables sans fiscalite immediate tant qu'ils restent dans le plan

## Step 7: Summary of the Simulated Workflow

| Etape | Action | Outil | Statut |
|-------|--------|-------|--------|
| 1 | Expliquer le skill | Message utilisateur | Simule |
| 2 | Recueillir la composition | Questions interactives | Simule (donnees fournies) |
| 3 | Chercher les ISINs | yfinance_search + get_ticker_info | Simule (ISINs connus) |
| 4 | Verifier eligibilite PEA | yfinance_get_ticker_info | Simule (eligibles confirmes) |
| 5 | Presenter le tableau | Template markdown | Simule (ci-dessus) |
| 6 | Questions de clarification | Dialogue interactif | Simule (questions listees) |
| 7 | Creer TRACKER.md | Write file | NON FAIT (test run) |
| 8 | Analyse technique (Phase 3) | yfinance + finance-trading-expert | Decrit ci-dessus |
| 9 | Recommandations | Selon strategie short/long | Decrit ci-dessus |
| 10 | Mise a jour TRACKER.md | Edit file | NON FAIT (test run) |

## Notes on This Test Run

- **TRACKER.md was NOT written to disk** per test instructions
- The ISINs used (FR0000120271 and NL0000226223) are the correct real-world ISINs for these companies
- Both stocks are confirmed PEA-eligible (French/EU domicile, traded on Euronext Paris)
- Total invested capital: 5 000 EUR (well within the 150 000 EUR PEA contribution limit)
- In a real session, the finance-trading-expert skill would be invoked for indicator formulas and interpretation
- In a real session, live price data from yfinance would drive the P&L calculations and recommendations
