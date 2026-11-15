# PEA Portfolio Tracker (fixture — date du jour : 2026-11-15)

## Account Information

| Field | Value |
|-------|-------|
| **Capital deployed** | €9 000,00 |
| **Available cash** | €3 000,00 |
| **Portfolio market value** | €9 400,00 |
| **Unrealized P&L** | +€400,00 |
| **Total PEA value** | €12 400,00 |
| **PEA opened** | 2019-11-07 |
| **PEA > 5 years** | Yes (7 years) |
| **Last review** | 2026-11-08 |

## Exceptions

| Name | ISIN | Reason |
|------|------|--------|

## Portfolio Composition

| Name | ISIN | Ticker | Nb Shares | PRU (€) | Strategy | Stop | Take-profit |
|------|------|--------|-----------|---------|----------|------|-------------|
| Norvia Défense | FR0014000AA1 | NRV.PA | 15 | 58.73 | short | 55,82 € — alerte seule | — |
| Calder Chimie | FR0014000BB2 | CLD.PA | 12 | 60.54 | short | 58,23 € — alerte seule | — |

## Closed Positions

| Name | Shares Sold | Sell Price (€) | PRU (€) | P&L (€) | P&L % |
|------|------------|----------------|---------|---------|-------|

## Thesis

### Norvia Défense (short)
- **Date entered**: 2026-09-09
- **Thesis**: Électronique de défense, carnet de commandes en hausse, réarmement européen.
- **Exit conditions**: Objectif +10-15 % brut (64,60-67,50 €). Alerte 55,82 € (1,5× ATR sous l'entrée).
- **Last reviewed**: 2026-11-08 — HOLD.

### Calder Chimie (short)
- **Date entered**: 2026-08-23
- **Thesis**: Chimie de spécialité, rotation vers les matériaux.
- **Exit conditions**: Alerte sortie 58,23 € (1,5× ATR sous l'entrée) → vente manuelle si cassée. Objectif 65,00 €.
- **Last reviewed**: 2026-11-08 — HOLD.

## Indicator output (fresh script output for this review; news cross-check on both names done 2026-11-14: GREEN, no company-specific news)

### Norvia Défense (NRV.PA)
```
POSITION: Norvia Défense (NRV.PA)
PRICE: €65.40 (source: yahoo)
P&L: +100.05€ (+11.4%)
RSI(14): 68.0 — [neutral] — [rising]
MACD: line 1.42, signal 1.10, histogram 0.32 — [bullish crossover on 2026-11-03]
BOLLINGER: upper 66.10, middle 62.40, lower 58.70 — price at 91% of band width — [upper-middle]
SMA: 50-day 60.73, 200-day 55.45 — [golden cross on 2026-07-02]
ATR(14): 2.02 — 1.5× ATR = 3.03 (4.6% from price)
VOLUME: avg 210,000 vs 20d avg 205,000 — [normal]
CHANGE: 5d +3.1%, 3m +9.8%
TAX (indicative, only on withdrawal): PEA >5 years (7.02y) — net after tax: +81.44€
```
### Calder Chimie (CLD.PA)
```
POSITION: Calder Chimie (CLD.PA)
PRICE: €57.05 (source: yahoo)
P&L: -41.88€ (-5.8%)
RSI(14): 44.0 — [neutral] — [falling]
MACD: line -0.31, signal -0.12, histogram -0.19 — [bearish crossover on 2026-11-06]
BOLLINGER: upper 60.20, middle 58.60, lower 57.00 — price at 2% of band width — [near lower]
SMA: 50-day 58.90, 200-day 59.80 — [death cross on 2026-10-16]
ATR(14): 1.22 — 1.5× ATR = 1.83 (3.2% from price)
VOLUME: avg 210,000 vs 20d avg 205,000 — [normal]
CHANGE: 5d -2.9%, 3m -6.0%
TAX (indicative, only on withdrawal): PEA >5 years (7.02y) — net after tax: -41.88€
```
### CAC 40 (^FCHI)
```
DUE DILIGENCE: CAC 40 (^FCHI)
PRICE: €8368.91 (source: yahoo)
SMA: 50-day 8028.81, 200-day 8207.84 — [death cross on 2026-10-15]
CHANGE: 5d +0.4%, 3m -1.7%
```
