#!/usr/bin/env python3
"""
Fetch daily OHLCV data from Yahoo Finance (chart API) and write it to a JSON
file in the parallel-array format expected by compute_indicators.py.

Why this exists: yfinance's MCP tool returns a markdown table, which forced each
pea-price-analyst / pea-dd-analyst agent to write a bespoke throwaway parser.
This script fetches the same data over plain HTTP as clean JSON, so the agents
run one deterministic command instead of generating scripts.

Usage:
  python3 fetch_ohlcv.py --ticker ENGI.PA --range 1y --out /tmp/pea_ohlcv_ENGI_PA.json

Defaults:
  --range 1y, --interval 1d. --out defaults to /tmp/pea_ohlcv_<TICKER>.json
  (dots replaced by underscores — ticker-unique, safe for parallel agents).

No external dependencies — stdlib only (urllib + json + datetime).

Exit codes: 0 on success, 1 on any error (fetch failure, empty data, bad JSON).
"""

import argparse
import datetime
import json
import sys
import urllib.parse
import urllib.request

YAHOO_CHART_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"


def fetch_json(url):
    """GET a URL and return parsed JSON. Raises on HTTP error or bad JSON."""
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_bars(ticker, rng="1y", interval="1d"):
    """Fetch daily bars for one ticker; return the parallel-array dict
    (dates/opens/highs/lows/closes/volumes). Raises RuntimeError on any failure."""
    url = YAHOO_CHART_URL.format(ticker=urllib.parse.quote(ticker)) + "?range={}&interval={}".format(rng, interval)
    try:
        payload = fetch_json(url)
    except Exception as e:
        raise RuntimeError("fetch failed for {}: {}".format(ticker, e))

    chart = payload.get("chart", {})
    error = chart.get("error")
    if error:
        raise RuntimeError("Yahoo returned error for {}: {}".format(ticker, error))

    results = chart.get("result") or []
    if not results:
        raise RuntimeError("no result for {} (ticker unknown or delisted?)".format(ticker))

    result = results[0]
    timestamps = result.get("timestamp") or []
    quotes = (result.get("indicators", {}).get("quote") or [{}])[0]

    opens = quotes.get("open") or []
    highs = quotes.get("high") or []
    lows = quotes.get("low") or []
    closes = quotes.get("close") or []
    volumes = quotes.get("volume") or []

    # Build parallel arrays, dropping bars with a null close (holidays, partial
    # last bar) so compute_indicators.py never sees NaN in the price series.
    dates, o_out, h_out, l_out, c_out, v_out = [], [], [], [], [], []
    for i, ts in enumerate(timestamps):
        if i >= len(closes) or closes[i] is None:
            continue
        try:
            dt = datetime.datetime.fromtimestamp(ts, tz=datetime.timezone.utc)
        except (ValueError, OSError, OverflowError):
            continue
        dates.append(dt.strftime("%Y-%m-%d"))
        o_out.append(opens[i] if i < len(opens) and opens[i] is not None else closes[i])
        h_out.append(highs[i] if i < len(highs) and highs[i] is not None else closes[i])
        l_out.append(lows[i] if i < len(lows) and lows[i] is not None else closes[i])
        c_out.append(closes[i])
        v_out.append(volumes[i] if i < len(volumes) and volumes[i] is not None else 0)

    if len(c_out) == 0:
        raise RuntimeError("no valid OHLCV bars for {}".format(ticker))

    return {"dates": dates, "opens": o_out, "highs": h_out, "lows": l_out,
            "closes": c_out, "volumes": v_out}


def main():
    parser = argparse.ArgumentParser(description="Fetch daily OHLCV from Yahoo Finance into a JSON file.")
    parser.add_argument("--ticker", "-t", required=True, help="Ticker in Yahoo format, e.g. ENGI.PA")
    parser.add_argument("--range", "-r", default="1y", help="Yahoo range (default 1y)")
    parser.add_argument("--interval", "-i", default="1d", help="Yahoo interval (default 1d)")
    parser.add_argument("--out", "-o", default=None, help="Output JSON path (default /tmp/pea_ohlcv_<TICKER>.json)")
    args = parser.parse_args()

    ticker = args.ticker.upper()
    out_path = args.out or "/tmp/pea_ohlcv_{}.json".format(ticker.replace(".", "_"))

    try:
        data = fetch_bars(ticker, args.range, args.interval)
    except RuntimeError as e:
        print("ERROR: {}".format(e), file=sys.stderr)
        sys.exit(1)

    with open(out_path, "w") as f:
        json.dump(data, f)

    print("OK {}: {} bars, last close {:.2f} ({}) -> {}".format(
        ticker, len(data["closes"]), data["closes"][-1], data["dates"][-1], out_path))


if __name__ == "__main__":
    main()
