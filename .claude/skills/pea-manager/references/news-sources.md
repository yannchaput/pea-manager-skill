# News Sources — Full Reference

This file contains the complete procedures for all news sources used by the PEA Manager skill. For the condensed decision table and quick-reference, see the News Sources section in SKILL.md.

---

## Primary: TradingView (via Playwright) — English, per-ticker, free

TradingView aggregates Reuters, Quartr (earnings transcripts/slides), and other sources. It is the best free source for European mid/small cap news. **This check is mandatory before any `short` entry recommendation.**

**Symbol format**: `EURONEXT:{TICKER}` for Euronext Paris stocks.
Examples: `EURONEXT:ATE` (Alten), `EURONEXT:AIR` (Airbus), `EURONEXT:DSY` (Dassault Systèmes).

**Procedure**:

1. Navigate to `https://www.tradingview.com/symbols/EURONEXT-{TICKER}/` (note the dash, not colon, in the URL)
2. Click the **News** tab: `getByRole('tab', { name: 'News' })`
3. Take a snapshot: `browser_snapshot()`
4. Extract and read all article titles, dates, and sources from the snapshot
5. Close the browser: `browser_close()`

**What to look for in the news**:
- Revenue/profit warnings (strongest sell signal)
- CEO or management departures (governance risk)
- Guidance cuts (organic growth going negative)
- Legal/regulatory issues
- Sector-wide headwinds (e.g., "automotive sector drag")
- Margin compression
- If multiple negative signals are present across different dates → the drop is **structural, not technical** → DO NOT buy the pullback

**Example — Alten (ATE), June 2026**:
The TradingView news page revealed a clear pattern hidden from English-only APIs:
- Net income −42.6% in FY 2025
- Organic growth guidance: 0% to −0.5% for H1 2026
- CEO replaced in October 2025
- Automotive sector −15%
- Legal risks flagged
→ These 5 signals across 6+ months of news make it clear: this was a structural decline, not a technical pullback. The low P/E was a value trap.

---

## Secondary: Investir Les Echos (via Playwright) — French, per-ticker, soft paywall

Investir (Les Echos group) is the most comprehensive French-language source for per-ticker news and stock data. It provides 30+ articles per stock, detailed financial indicators, analyst consensus, and editorial analysis. **Headlines and article previews are visible without subscription** — the first 2-3 paragraphs of each article provide enough context for a buy/skip decision.

**Symbol format**: URL is `https://investir.lesechos.fr/cours/actions/{name}-{symbol}-{isin}-xpar`
- Example for Alten: `https://investir.lesechos.fr/cours/actions/alten-ate-fr0000071946-xpar`
- The ISIN is required. Get it from EODHD `get_fundamentals_data` → `General.ISIN` or construct it from the ticker.

**Stock page sections** (all visible without subscription):

| Section | Content | Utility |
|---------|---------|---------|
| **Dernières actualités** | 10+ article headlines with dates and sources (AFP, Agefi-Dow Jones, Reuters, Conseil de la rédaction) | 🏆 Primary signal source — scan headlines for profit warnings, guidance cuts, CEO changes |
| **Actualités & conseils** (sub-page) | 30+ articles dating back 8+ months | Deep dive into stock's news history to identify structural trends |
| **Recommandations** | Analyst ratings and target prices | Cross-check analyst sentiment |
| **Statistiques de cours** | Price stats (high/low, volatility, volumes) | Technical context |
| **Indicateurs financiers** | Key ratios (P/E, P/B, dividend yield, etc.) | Fundamental context |
| **Variations historiques** | Historical price performance | Trend analysis |
| **Graphique** | Interactive price chart | Visual trend confirmation |

**Access levels**:
- **Free (no account)**: All headlines, stock data, statistics, chart, first 2-3 paragraphs of wire articles (Reuters, Agefi-Dow Jones)
- **Free registration**: Full wire articles (AFP, Reuters, Dow Jones)
- **Paid subscription** (3.49€/month): "Conseil de la rédaction" (editorial stock picks and analysis)

**Procedure for the per-ticker news check**:

1. Navigate to the stock page: `https://investir.lesechos.fr/cours/actions/{name}-{symbol}-{isin}-xpar`
2. Wait for page load: `waitForTimeout(2000)`
3. If cookie wall appears, click "Accepter" or navigate past it (the page content is visible behind it)
4. Extract headlines from "Dernières actualités" section:
   ```js
   const articles = await page.evaluate(() => {
     const links = document.querySelectorAll('a');
     return Array.from(links)
       .filter(l => l.textContent.length > 25 && l.href.includes('investir.lesechos.fr'))
       .map(l => ({ title: l.textContent.trim().substring(0, 200), url: l.href }))
       .slice(0, 15);
   });
   ```
5. Navigate to the `/actualites-conseils` sub-page for full history (30+ articles)
6. Read article previews (first 2-3 paragraphs) for context on key headlines
7. Close the browser: `browser_close()`

**What Investir provides that other sources don't**:
- French-language editorial analysis ("Conseil de la rédaction") — even the headline alone signals the editorial stance
- French market context — sector trends, CAC 40 comparisons, French economic angle
- "La vie des actions" — corporate events (buybacks, governance changes, M&A)
- Mix of sources: AFP + Agefi-Dow Jones + Reuters + in-house analysts on one page
- 8+ months of news history on the actualités sub-page

**Example — Alten (ATE), June 2026**:
Investir headlines revealed the same structural decline pattern as TradingView, but with French context:
- Apr 28: "Alten vise une croissance organique entre 0% et -0.5% en 2026" (AFP)
- Apr 28: "Alten anticipe une croissance organique entre 0% et -0.5% au S1" (Reuters)
- Mar 12: "Alten : du retard au rallumage" (Conseil de la rédaction)
- Mar 4: "Alten sortira de l'indice Stoxx Europe 600 le 23 mars" (Agefi-Dow Jones)
- Feb 24: "Alten — Baisse de 42.6% du résultat net en 2025" (Reuters)
- Sep 2025: "Alten nomme Cyril Malargé (ex-Sopra Steria) au poste de DG"
→ These headlines alone would have been sufficient to flag the value trap, even without reading full articles.

---

## Tertiary: Boursier.com (via Playwright) — French, market-level, free

Boursier.com provides French-language market sentiment and analyst recommendations. Per-ticker news is limited, but the fil info and analyst recos sections are useful for broad market context.

**Sections that work**:

| Section | URL | What it provides |
|---------|-----|-------------------|
| **Fil info du jour** | `https://www.boursier.com/actualites/news-du-jour` | Last 24h headlines in French with timestamps (~25 articles). Best for checking overall market sentiment. |
| **Recommandations analystes** | `https://www.boursier.com/actualites/avis-brokers` | Analyst rating changes — titles visible, full content requires subscription. Useful even in truncated form to spot rating upgrades/downgrades. |
| **Cours par société** | `https://www.boursier.com/actions/cours/{name}-{ISIN},FR.html` | Price, order book, analyst consensus, technical indicators. Good for data cross-checking when both yfinance and EODHD fail. |

**Sections that do NOT work** (JS lazy-loading, paywall):
- "A lire aussi sur {ticker}" — widget AJAX, stuck on "Chargement en cours..."
- Search by ticker — JS templates unresolved
- Small&Mid Caps section — XHR lazy-load, never renders
- Full articles — paywall wall: "Disposez des meilleures informations" → login required

**Procedure for the fil info check**:
1. Navigate to `https://www.boursier.com/actualites/news-du-jour`
2. Wait 2 seconds for JS hydration: `waitForTimeout(2000)`
3. Extract: `document.querySelectorAll('.item')` → map to `.textContent.trim()`
4. Scan headlines for the target ticker, sector, or relevant themes
5. Close the browser

---

## Quaternary: EODHD `get_company_news` and Yahoo Finance `get_ticker_news` — English, API, quick

Use these for quick English-language checks via API (no Playwright needed). They rarely cover French mid/small caps but can catch Reuters headlines for larger stocks (CAC 40). Only rely on them when the TradingView, Investir, and Boursier.com checks have already been done, or for large caps where they pick up Reuters coverage.

---

## Known Limitations

- **French financial sites block automation**: Boursorama, Zonebourse block direct `WebFetch` (403 Forbidden). Playwright works around this. Investir and Boursier.com work with Playwright.
- **Investir**: Cookie consent wall (Didomi) on first visit. "Conseil de la rédaction" articles require paid subscription (3.49€/month). Wire articles (AFP, Reuters, Agefi-Dow Jones) require free registration for full text — but headlines + first paragraphs are visible without any account.
- **Boursier.com**: Per-ticker content is limited (AJAX lazy-load, JS template rendering). Best used for market-level sentiment, not individual stock news.
- **TradingView**: English-only. No French-language context.
- **Playwright adds latency**: Each check takes ~15-25 seconds. For a full portfolio review, budget ~5 minutes extra if checking all positions. Investir check with actualités sub-page takes ~25-35 seconds.
- **Always close the browser tab** after each check to avoid resource leaks (`browser_close()`)
- **No single source covers everything**: Investir = best French per-ticker. TradingView = best English per-ticker. Boursier.com = best French market sentiment. EODHD/Yahoo = quick API backup. Use all four for a complete picture.
