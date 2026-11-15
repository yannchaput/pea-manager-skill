#!/usr/bin/env python3
"""
Phase 4 discovery: scan a fixed universe of PEA-eligible European stocks with
free Yahoo data and rank them with the trend-aware LL-01 score.

Why this exists: the EODHD exchange-browse agent could not do this job. The
listing tool has no market-cap/price/sector filter and returns whole exchanges
(hundreds of thousands of characters), so scans fell back on model memory.
Here the universe is a file (assets/universe.json), the data is the Yahoo chart API
(no key, no quota) and the screening is code, not an LLM.

Usage:
  python3 scan_universe.py [--bucket large|mid|all] [--top 25] [--workers 8]

Output: stocks not already in TRACKER.md (by ticker or name, so recently closed or rejected names are skipped too), grouped PASS (ENTER, no gate),
WATCH (uptrend, partial confirmations) and GATED (downtrend/overbought).
Survivors still need fundamentals (yfinance info) and the news cross-check.

shortcut: bucket (large/mid) is a hand-assigned index-membership proxy for
market cap, not a live figure; refresh assets/universe.json when index changes matter.
Stdlib only. Exit 0 always; unfetchable tickers are listed at the end.
"""

import argparse
import json
import math
import re
import sys
import unicodedata
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import compute_indicators as ci
from fetch_ohlcv import fetch_bars

HERE = Path(__file__).resolve().parent
TRACKER = HERE.parents[3] / "TRACKER.md"  # scripts/ -> pea-manager -> skills -> .claude -> repo root
# Same list as references/pea-eligibility.md (EU + EEA)
PEA_COUNTRIES = set("AT BE BG HR CY CZ DK EE FI FR DE GR HU IE IT LV LT LU MT NL PL PT RO SK SI ES SE IS LI NO".split())
TICKER_RE = re.compile(r"\b[A-Z0-9]{1,6}\.[A-Z]{2}\b")


def tracked_tickers(tracker_text):
    """Every Yahoo-style ticker (XXX.PA) mentioned in TRACKER.md."""
    return set(TICKER_RE.findall(tracker_text))


def is_tracked(row, tracker_text, tickers):
    """True if the stock is in TRACKER.md by ticker or by name (accent/case-insensitive,
    whole word). Needed because several held positions carry no ticker line."""
    if row["ticker"] in tickers:
        return True
    fold = lambda t: unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode().lower()
    return re.search(r"\b" + re.escape(fold(row["name"])) + r"\b", fold(tracker_text)) is not None


def evaluate(bars):
    """Score one stock's bars with the same rules as `compute_indicators.py --mode dd`.

    Returns a dict, or None if the history is too short for the indicators."""
    closes, highs, lows, vols = bars["closes"], bars["highs"], bars["lows"], bars["volumes"]
    if len(closes) < 60:
        return None
    price = closes[-1]
    rsi, _ = ci.compute_rsi(closes)
    _, _, macd_hist, _, cross_type, cross_bars = ci.compute_macd(closes)
    _, _, _, bb_pct = ci.compute_bollinger(closes)
    _, _, atr_pct = ci.compute_atr(highs, lows, closes)
    _, _, vol_pct, _ = ci.compute_volume(vols)
    sma50, sma200 = ci.sma(closes, 50)[-1], ci.sma(closes, 200)[-1]
    gate = ci.ll01_gate_reason(price, sma50, sma200, rsi)
    conf, atr_pass, rec = ci.score_ll01(
        rsi, macd_hist, 0 if math.isnan(vol_pct) else vol_pct, bb_pct, atr_pct, price, gate_reason=gate)
    ret_3m = (price / closes[-64] - 1) * 100 if len(closes) > 64 else float("nan")
    return dict(price=price, rsi=rsi, conf=conf, atr_pass=atr_pass, rec=rec, gate=gate,
                ret_3m=ret_3m, off_high=(price / max(closes) - 1) * 100,
                above_sma200=None if math.isnan(sma200) else price > sma200)


def scan_one(row):
    """Fetch and evaluate one universe row; returns (row, result|None, error|None)."""
    try:
        return row, evaluate(fetch_bars(row["ticker"])), None
    except RuntimeError as e:
        return row, None, str(e)


def group(res):
    """PASS = ENTER without gate; GATED = capped by trend/overbought; else WATCH."""
    if res["gate"]:
        return "GATED"
    return "PASS" if res["rec"] == "ENTER" else "WATCH"


def main():
    ap = argparse.ArgumentParser(description="Scan the PEA universe with the trend-aware LL-01 score.")
    ap.add_argument("--bucket", choices=["large", "mid", "all"], default="all")
    ap.add_argument("--top", type=int, default=25, help="max rows printed per group")
    ap.add_argument("--workers", type=int, default=8)
    args = ap.parse_args()

    universe = json.loads((HERE.parent / "assets" / "universe.json").read_text())
    text = TRACKER.read_text() if TRACKER.exists() else ""
    held = tracked_tickers(text)
    rows = [r for r in universe
            if not is_tracked(r, text, held) and r["country"] in PEA_COUNTRIES
            and args.bucket in ("all", r["bucket"])]

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        out = list(pool.map(scan_one, rows))

    scored = [(r, res) for r, res, err in out if res]
    failed = [r["ticker"] + ": " + err for r, res, err in out if err]
    short = [r["ticker"] for r, res, err in out if not res and not err]
    print(f"Scanned {len(scored)}/{len(rows)} (excluded {len(universe) - len(rows)} held/tracked/ineligible)")

    for g in ("PASS", "WATCH", "GATED"):
        items = sorted((x for x in scored if group(x[1]) == g),
                       key=lambda x: (-x[1]["conf"], x[1]["ret_3m"]))
        print(f"\n== {g} ({len(items)}) ==")
        print(f"{'ticker':<10} {'name':<24} {'bkt':<5} {'price':>8} {'RSI':>5} {'ll01':>4} {'3m%':>6} {'vs high':>8}  note")
        for r, res in items[:args.top]:
            note = res["gate"] or ("above SMA200" if res["above_sma200"] else "")
            print(f"{r['ticker']:<10} {r['name'][:24]:<24} {r['bucket']:<5} {res['price']:>8.2f} "
                  f"{res['rsi']:>5.1f} {res['conf']:>3}/4 {res['ret_3m']:>6.1f} {res['off_high']:>7.1f}%  {note}")
    if short:
        print("\nToo little history:", ", ".join(short))
    if failed:
        print("\nFetch failures (check ticker in assets/universe.json):\n  " + "\n  ".join(failed))


if __name__ == "__main__":
    sys.exit(main())
