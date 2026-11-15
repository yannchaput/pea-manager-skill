#!/usr/bin/env python3
"""
Compute technical indicators from OHLCV data for PEA portfolio positions.

Usage:
  python3 compute_indicators.py --fetch \
    --name "Air Liquide" --ticker "AI.PA" \
    --shares 44 --pru 139.755 --pea-years 6.83

--fetch pulls 1y of daily bars from Yahoo in-process. Without it, bars are read
from --input FILE or stdin (see "Input" below), e.g. after an EODHD fallback.

--pea-years takes a plain number (age of the PEA in years since opening).
Tax rate is derived automatically (>=5 years -> 18.6% PS only, <5 years -> 31.4%
PFU) — never pass the rate or a ">"/"<" comparison string here: on the command
line ">" is a shell redirection operator, and even when quoted correctly, an
LLM-driven caller reformatting free text like ">5 years (6y10m)" into a shell
argument has repeatedly dropped the leading ">" silently, which flips every
position's net P&L to the wrong tax rate without erroring. A plain float
sidesteps both failure modes.

Input (--input or stdin): JSON object with parallel arrays:
  {"dates": [...], "opens": [...], "highs": [...], "lows": [...],
   "closes": [...], "volumes": [...]}

Output: structured text block with all indicators + P&L for the main agent.

No external dependencies — stdlib only.
"""

import argparse
import json
import math
import sys


# ---------------------------------------------------------------------------
# Moving averages
# ---------------------------------------------------------------------------

def sma(values, period):
    """Simple moving average. Returns list same length as values, with NaN for
    indices < period-1."""
    out = [float("nan")] * len(values)
    if len(values) < period:
        return out
    window_sum = sum(values[:period])
    out[period - 1] = window_sum / period
    for i in range(period, len(values)):
        window_sum += values[i] - values[i - period]
        out[i] = window_sum / period
    return out


def ema(values, period):
    """Exponential moving average (Wilder's variant: alpha = 1/period).
    Seed = SMA of first `period` values. Returns list same length as values."""
    out = [float("nan")] * len(values)
    if len(values) < period:
        return out
    alpha = 1.0 / period
    seed = sum(values[:period]) / period
    out[period - 1] = seed
    for i in range(period, len(values)):
        out[i] = out[i - 1] * (1 - alpha) + values[i] * alpha
    return out


def ema_standard(values, period):
    """Standard EMA: alpha = 2/(period+1). Seed = SMA of first `period` values."""
    out = [float("nan")] * len(values)
    if len(values) < period:
        return out
    alpha = 2.0 / (period + 1)
    seed = sum(values[:period]) / period
    out[period - 1] = seed
    for i in range(period, len(values)):
        out[i] = out[i - 1] * (1 - alpha) + values[i] * alpha
    return out


# ---------------------------------------------------------------------------
# Technical indicators
# ---------------------------------------------------------------------------

def rsi_series(closes, period=14):
    """Wilder's smoothed RSI, one value per bar from index `period`. [] if too short."""
    if len(closes) < period + 1:
        return []
    deltas = [closes[i] - closes[i - 1] for i in range(1, len(closes))]
    gains = [max(d, 0) for d in deltas]
    losses = [max(-d, 0) for d in deltas]
    avg_gain = sum(gains[:period]) / period  # seed: simple average
    avg_loss = sum(losses[:period]) / period
    out = []
    for i in range(period - 1, len(gains)):
        if i >= period:
            avg_gain = (avg_gain * (period - 1) + gains[i]) / period
            avg_loss = (avg_loss * (period - 1) + losses[i]) / period
        out.append(100.0 if avg_loss == 0 else 100.0 - 100.0 / (1.0 + avg_gain / avg_loss))
    return out


def compute_rsi(closes, period=14):
    """Latest RSI. Returns (rsi_value, trend); trend is 'rising' | 'falling' |
    'stable' from the last 5 RSI values (a move of more than 2 points)."""
    values = rsi_series(closes, period)
    if not values:
        return float("nan"), "stable"
    recent = values[-5:]
    if recent[-1] > recent[0] + 2:
        trend = "rising"
    elif recent[-1] < recent[0] - 2:
        trend = "falling"
    else:
        trend = "stable"
    return round(values[-1], 1), trend


def compute_macd(closes, dates=None, fast=12, slow=26, signal=9):
    """Standard MACD (EMA alpha = 2/(n+1)): fast EMA - slow EMA, signal line, histogram.

    Returns (macd_line, signal_line, histogram, crossover_date, crossover_type,
    bars_since_cross) for the most recent crossover.

    crossover_type is 'bullish' | 'bearish' | 'none'; crossover_date is the date
    string or 'N/A' (always 'N/A' without `dates`); bars_since_cross is an int
    (0 = crossover on the last bar) or None when there is no crossover.
    """
    nan = float("nan")
    if len(closes) < slow + signal:
        return nan, nan, nan, "N/A", "none", None

    ema_fast = ema_standard(closes, fast)
    ema_slow = ema_standard(closes, slow)
    start = slow - 1  # first bar where both EMAs exist
    macd = [f - s for f, s in zip(ema_fast[start:], ema_slow[start:])]
    sig = ema_standard(macd, signal)

    crossover_date, crossover_type, bars_since = "N/A", "none", None
    for i in range(signal, len(macd)):  # sig[i-1] is valid from i = signal
        if macd[i - 1] <= sig[i - 1] and macd[i] > sig[i]:
            crossover_type = "bullish"
        elif macd[i - 1] >= sig[i - 1] and macd[i] < sig[i]:
            crossover_type = "bearish"
        else:
            continue
        bars_since = len(macd) - 1 - i
        crossover_date = dates[start + i] if dates and start + i < len(dates) else "N/A"

    return (round(macd[-1], 2), round(sig[-1], 2), round(macd[-1] - sig[-1], 2),
            crossover_date, crossover_type, bars_since)


def compute_bollinger(closes, period=20, num_std=2):
    """Bollinger Bands. Returns (upper, middle, lower, band_pct).

    band_pct = (price - lower) / (upper - lower) * 100
    """
    if len(closes) < period:
        return float("nan"), float("nan"), float("nan"), float("nan")

    sma20 = sma(closes, period)
    middle = sma20[-1]
    if math.isnan(middle):
        return float("nan"), float("nan"), float("nan"), float("nan")

    recent = closes[-period:]
    mean = sum(recent) / period
    variance = sum((x - mean) ** 2 for x in recent) / (period - 1)  # sample std
    std = math.sqrt(variance)

    upper = middle + num_std * std
    lower = middle - num_std * std
    band_width = upper - lower
    price = closes[-1]

    if band_width > 0:
        band_pct = (price - lower) / band_width * 100
    else:
        band_pct = 50.0  # degenerate case

    return round(upper, 2), round(middle, 2), round(lower, 2), round(band_pct, 0)


def compute_atr(highs, lows, closes, period=14):
    """Average True Range (Wilder's smoothing). Returns (atr, atr_1_5x, pct_from_price)."""
    if len(closes) < period + 1:
        return float("nan"), float("nan"), float("nan")

    true_ranges = []
    for i in range(1, len(closes)):
        h, l, prev_c = highs[i], lows[i], closes[i - 1]
        tr = max(h - l, abs(h - prev_c), abs(l - prev_c))
        true_ranges.append(tr)

    atr_series = ema(true_ranges, period)
    atr_val = atr_series[-1] if not math.isnan(atr_series[-1]) else float("nan")
    atr_1_5x = atr_val * 1.5 if not math.isnan(atr_val) else float("nan")
    pct = (atr_1_5x / closes[-1] * 100) if not (math.isnan(atr_val) or closes[-1] == 0) else float("nan")

    return (round(atr_val, 2) if not math.isnan(atr_val) else float("nan"),
            round(atr_1_5x, 2) if not (math.isnan(atr_1_5x) if isinstance(atr_1_5x, float) else True) else float("nan"),
            round(pct, 1) if not (math.isnan(pct) if isinstance(pct, float) else True) else float("nan"))


def compute_sma_cross(sma50_series, sma200_series, dates):
    """Determine golden/death cross status and date.

    Uses the last valid SMA50 and SMA200 to determine current alignment.
    Scans for the most recent cross event.
    Returns (status, cross_date).
    """
    # Get current status
    sma50_last = sma50_series[-1] if not math.isnan(sma50_series[-1]) else None
    sma200_last = sma200_series[-1] if not math.isnan(sma200_series[-1]) else None

    if sma50_last is None or sma200_last is None:
        return "N/A", "N/A"

    current_alignment = "golden" if sma50_last > sma200_last else "death"

    # Scan for most recent cross
    cross_date = "N/A"
    for i in range(1, len(sma50_series)):
        p50 = sma50_series[i - 1]
        p200 = sma200_series[i - 1]
        c50 = sma50_series[i]
        c200 = sma200_series[i]
        if math.isnan(p50) or math.isnan(p200) or math.isnan(c50) or math.isnan(c200):
            continue
        if p50 <= p200 and c50 > c200:
            cross_date = dates[i] if i < len(dates) else "N/A"
        elif p50 >= p200 and c50 < c200:
            cross_date = dates[i] if i < len(dates) else "N/A"

    status = f"golden cross" if current_alignment == "golden" else "death cross"
    return status, cross_date


def compute_volume(volumes):
    """Analyze volume: recent 5d avg vs 20d avg. Returns (recent_daily, avg20d, pct_diff, label)."""
    if len(volumes) < 5:
        return float("nan"), float("nan"), float("nan"), "N/A"

    # Most recent complete day is usually second-to-last (last may be partial)
    # We use last-5 vs 20d avg, excluding the very last partial day
    recent_5 = volumes[-6:-1] if len(volumes) >= 6 else volumes[-5:]
    period_20 = max(5, min(20, len(volumes)))
    avg20 = volumes[-period_20:]

    if not avg20 or sum(avg20) == 0:
        return float("nan"), float("nan"), float("nan"), "N/A"

    recent_avg = sum(recent_5) / len(recent_5) if recent_5 else 0
    avg20_avg = sum(avg20) / len(avg20)
    pct_diff = ((recent_avg - avg20_avg) / avg20_avg * 100) if avg20_avg > 0 else 0

    if pct_diff > 50:
        label = f"elevated (+{round(pct_diff)}%)"
    elif pct_diff < -30:
        label = f"subdued ({round(pct_diff)}%)"
    else:
        label = "normal"

    return int(recent_avg), int(avg20_avg), round(pct_diff, 1), label


def change_pct(closes, n):
    """Percent change of the last close vs n bars earlier. NaN if history is too short."""
    if len(closes) <= n:
        return float("nan")
    return (closes[-1] / closes[-1 - n] - 1) * 100


def compute_rr(entry, target, stop):
    """Risk/Reward ratio. Returns float or NaN if any input missing."""
    if entry is None or target is None or stop is None:
        return float("nan")
    if entry <= 0 or target <= 0 or stop <= 0:
        return float("nan")
    reward = target - entry
    risk = entry - stop
    if risk <= 0:
        return float("nan")
    return round(reward / risk, 1)


def analyze_trend(closes):
    """Analyze price structure over last 3 months.
    Returns (trend_label, trend_sentence)."""
    if len(closes) < 40:
        return "N/A", "Not enough data for trend analysis"

    # Use last ~60 bars (~3 months)
    window = closes[-60:] if len(closes) >= 60 else closes
    half = len(window) // 2
    first_half = window[:half]
    second_half = window[half:]

    # Find swing highs (local maxima) in each half
    def find_swing_highs(prices):
        highs = []
        for i in range(1, len(prices) - 1):
            if prices[i] > prices[i-1] and prices[i] > prices[i+1]:
                highs.append(prices[i])
        return highs

    first_highs = find_swing_highs(first_half)
    second_highs = find_swing_highs(second_half)

    # Also compare simple highs of each half
    first_max = max(first_half)
    second_max = max(second_half)

    if not first_highs or not second_highs:
        if second_max > first_max * 1.03:
            return "higher-highs", "Price making higher highs — uptrend intact"
        elif second_max < first_max * 0.97:
            return "lower-highs", "Price making lower highs — downtrend or consolidation"
        else:
            return "range-bound", "Price oscillating in a range — no clear trend direction"

    first_avg_high = sum(first_highs) / len(first_highs)
    second_avg_high = sum(second_highs) / len(second_highs)

    if second_avg_high > first_avg_high * 1.02:
        return "higher-highs", "Swing highs rising — uptrend intact over trailing 3 months"
    elif second_avg_high < first_avg_high * 0.98:
        return "lower-highs", "Swing highs declining — downtrend or distribution phase"
    else:
        return "range-bound", "Swing highs stable — price consolidating in a range"


def compute_support_resistance(closes, highs, lows):
    """Identify top 2 support and resistance zones from swing points.
    Returns (s1, s2, r1, r2) as display strings "€x.xx (strength)" or "N/A";
    strength is 'strong' | 'moderate' | 'weak'."""
    if len(closes) < 20:
        return "N/A", "N/A", "N/A", "N/A"

    # Find swing lows (support) and swing highs (resistance)
    def find_swings(prices, find_highs=True):
        """Find swing points. find_highs=True for resistance, False for support."""
        swings = []
        for i in range(1, len(prices) - 1):
            if find_highs:
                if prices[i] > prices[i-1] and prices[i] > prices[i+1]:
                    swings.append(prices[i])
            else:
                if prices[i] < prices[i-1] and prices[i] < prices[i+1]:
                    swings.append(prices[i])
        return swings

    swing_highs = find_swings(highs[-60:], find_highs=True)
    swing_lows = find_swings(lows[-60:], find_highs=False)

    # Cluster within 2% tolerance, count touches for strength
    def cluster_and_rank(points):
        if not points:
            return []
        points = sorted(points, reverse=True)  # descending
        clusters = []
        for p in points:
            placed = False
            for cluster in clusters:
                center = sum(cluster) / len(cluster)
                if abs(p - center) / center < 0.02:
                    cluster.append(p)
                    placed = True
                    break
            if not placed:
                clusters.append([p])
        # Rank by cluster size (touches), then by price level
        ranked = sorted(clusters, key=lambda c: (len(c), sum(c)/len(c)), reverse=True)
        return [(sum(c)/len(c), len(c)) for c in ranked[:2]]

    resistance = cluster_and_rank(swing_highs)
    support = cluster_and_rank(swing_lows)

    def strength_label(touches):
        if touches >= 3:
            return "strong"
        elif touches >= 2:
            return "moderate"
        else:
            return "weak"

    r1, r1_touches = resistance[0] if len(resistance) > 0 else ("N/A", 0)
    r2, r2_touches = resistance[1] if len(resistance) > 1 else ("N/A", 0)
    s1, s1_touches = support[0] if len(support) > 0 else ("N/A", 0)
    s2, s2_touches = support[1] if len(support) > 1 else ("N/A", 0)

    r1_str = f"€{r1:.2f} ({strength_label(r1_touches)})" if r1 != "N/A" else "N/A"
    r2_str = f"€{r2:.2f} ({strength_label(r2_touches)})" if r2 != "N/A" else "N/A"
    s1_str = f"€{s1:.2f} ({strength_label(s1_touches)})" if s1 != "N/A" else "N/A"
    s2_str = f"€{s2:.2f} ({strength_label(s2_touches)})" if s2 != "N/A" else "N/A"

    return s1_str, s2_str, r1_str, r2_str


def ll01_gate_reason(price, sma50, sma200, rsi_val, rr=None):
    """Return why a stock must not be scored ENTER, or None.

    The 4-point score below is a snapshot and blind to trend, so it gave ENTER
    to stocks in a downtrend (LL-01/LL-02) or already overbought. Unknown SMAs
    (short history) do not gate: we cannot judge the trend. Neither does an
    unknown R/R (no target given)."""
    if rsi_val is not None and not math.isnan(rsi_val) and rsi_val >= 70:
        return "overbought (RSI >= 70)"
    if not (math.isnan(sma50) or math.isnan(sma200)) and sma50 < sma200 and price < sma200:
        return "downtrend (death-cross state and price below SMA200)"
    if rr is not None and not math.isnan(rr) and rr < 2:
        return f"risk/reward below 2 (R/R {rr:.1f})"
    return None


LL01_WINDOW = 10  # bars: how recent an RSI recovery or MACD crossover must be


def score_ll01(closes, opens, volumes, macd_hist, macd_cross_type, macd_bars_since,
               atr_pct, gate_reason=None):
    """Score the four LL-01 technical confirmations as the checklist words them.

    Returns (confirmations, atr_pass, recommendation, detail). detail maps each
    confirmation to a bool:
      rsi_recovery   RSI was <= 30 within LL01_WINDOW bars and is now > 30
      macd_cross     bullish MACD crossover within LL01_WINDOW bars, histogram still > 0
      volume_candle  one of the last 3 bars is green with volume > 1.5x the mean of
                     the 20 bars before it
      above_ema5     last close above the 5-day EMA
    recommendation is 'ENTER' (>= 2 confirmations, ATR pass, no gate) | 'WATCH'
    (>= 1) | 'SKIP'. A gate_reason (see ll01_gate_reason) caps ENTER at WATCH.
    Missing data (short history, NaN) scores the item False; it never raises."""
    rsi = rsi_series(closes)
    ema5 = ema_standard(closes, 5)[-1] if closes else float("nan")

    def green_volume_bar(i):
        prior = volumes[max(0, i - 20):i]
        return (len(prior) == 20 and closes[i] > opens[i]
                and volumes[i] > 1.5 * sum(prior) / 20)

    detail = {
        "rsi_recovery": bool(rsi) and min(rsi[-LL01_WINDOW:]) <= 30 < rsi[-1],
        "macd_cross": (macd_cross_type == "bullish" and macd_bars_since is not None
                       and macd_bars_since <= LL01_WINDOW and macd_hist > 0),
        "volume_candle": any(green_volume_bar(i) for i in range(max(0, len(closes) - 3), len(closes))),
        "above_ema5": bool(closes) and closes[-1] > ema5,  # NaN compares False
    }
    confirmations = sum(detail.values())

    # ATR check: 1.5x ATR must be <= 10% of entry price
    atr_pass = atr_pct is not None and not math.isnan(atr_pct) and atr_pct <= 10.0

    if confirmations >= 2 and atr_pass and not gate_reason:
        recommendation = "ENTER"
    elif confirmations >= 1:
        recommendation = "WATCH"
    else:
        recommendation = "SKIP"
    return confirmations, atr_pass, recommendation, detail


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Compute technical indicators for PEA position.")
    parser.add_argument("--mode", default="phase3", choices=["phase3", "dd"],
                        help="Analysis mode: phase3 (existing position) or dd (due diligence)")
    parser.add_argument("--name", required=True, help="Position/stock name")
    parser.add_argument("--ticker", required=True, help="Ticker symbol")
    parser.add_argument("--shares", type=float, default=0,
                        help="Number of shares (phase3 only)")
    parser.add_argument("--pru", type=float, default=0,
                        help="Average cost basis in EUR (phase3 only)")
    parser.add_argument("--pea-years", type=float, default=None,
                        help="PEA age in years as a plain number, e.g. 6.83 (phase3 only). "
                             "Determines the tax rate: >=5 -> 18.6%% PS only, <5 -> 31.4%% PFU.")
    parser.add_argument("--pea-age", default="",
                        help="Optional free-text label for the PEA age shown in the output "
                             "(e.g. '6 years 10 months'). Cosmetic only — does NOT affect the "
                             "tax rate; use --pea-years for that.")
    parser.add_argument("--source", default="yfinance", help="Data source name (yfinance/eodhd)")
    parser.add_argument("--entry-price", type=float, default=None,
                        help="Planned entry price in EUR (dd mode)")
    parser.add_argument("--target", type=float, default=None,
                        help="Profit target price in EUR (dd mode)")
    parser.add_argument("--stop", type=float, default=None,
                        help="Stop loss price in EUR (dd mode, auto-computed from ATR if omitted)")
    parser.add_argument("--input", "-i", default=None, help="Path to JSON input file (default: stdin)")
    parser.add_argument("--fetch", action="store_true",
                        help="Fetch 1y of daily bars for --ticker from Yahoo in-process "
                             "(no temp file, safe for parallel runs)")
    args = parser.parse_args()
    if args.fetch and args.input:
        parser.error("--fetch and --input are mutually exclusive")

    # Validate mode-specific requirements
    if args.mode == "phase3":
        if args.shares <= 0:
            print("ERROR: --shares required for phase3 mode", file=sys.stderr)
            sys.exit(1)
        if args.pru <= 0:
            print("ERROR: --pru required for phase3 mode", file=sys.stderr)
            sys.exit(1)
        if args.pea_years is None:
            print("ERROR: --pea-years required for phase3 mode (plain number of years, "
                  "e.g. 6.83 — do not use --pea-age for tax logic, it is display-only)",
                  file=sys.stderr)
            sys.exit(1)

    # Read input
    if args.fetch:
        from fetch_ohlcv import fetch_bars
        try:
            data = fetch_bars(args.ticker, "1y")
        except RuntimeError as e:
            print("ERROR: {}".format(e), file=sys.stderr)
            sys.exit(1)
    elif args.input:
        with open(args.input, "r") as f:
            data = json.load(f)
    else:
        data = json.load(sys.stdin)

    # Unpack OHLCV arrays
    dates = data.get("dates", [])
    opens = data.get("opens", [])
    highs = data.get("highs", [])
    lows = data.get("lows", [])
    closes = data.get("closes", [])
    volumes = data.get("volumes", [])

    n = len(closes)
    if n < 14:
        print("ERROR: Not enough data points (need at least 14, got {})".format(n), file=sys.stderr)
        sys.exit(1)

    current_price = closes[-1]

    # Compute all indicators
    rsi_val, rsi_trend = compute_rsi(closes)

    macd_line, macd_signal, macd_hist, cross_date, cross_type, cross_bars = compute_macd(closes, dates)
    cross_label = f"{cross_type} crossover on {cross_date}" if cross_type != "none" else "none"

    bb_upper, bb_middle, bb_lower, bb_pct = compute_bollinger(closes)
    if bb_pct >= 95:
        bb_zone = "near upper"
    elif bb_pct <= 5:
        bb_zone = "near lower"
    elif 45 <= bb_pct <= 55:
        bb_zone = "middle"
    elif bb_pct > 55:
        bb_zone = "upper-middle"
    else:
        bb_zone = "lower-middle"

    sma50 = sma(closes, 50)
    sma200 = sma(closes, 200)
    sma_status, sma_cross_date = compute_sma_cross(sma50, sma200, dates)
    sma50_val = round(sma50[-1], 2) if not math.isnan(sma50[-1]) else "N/A"
    sma200_val = round(sma200[-1], 2) if not math.isnan(sma200[-1]) else "N/A"

    atr_val, atr_1_5x, atr_pct = compute_atr(highs, lows, closes)
    vol_recent, vol_avg20, vol_pct_diff, vol_label = compute_volume(volumes)

    # RSI zone
    if rsi_val >= 70:
        rsi_zone = "overbought"
    elif rsi_val <= 30:
        rsi_zone = "oversold"
    else:
        rsi_zone = "neutral"

    # Volume display
    if not math.isnan(vol_recent):
        vol_display = f"avg {vol_recent:,} vs 20d avg {vol_avg20:,} — [{vol_label}]"
    else:
        vol_display = "N/A"

    change_line = f"CHANGE: 5d {change_pct(closes, 5):+.1f}%, 3m {change_pct(closes, 63):+.1f}%"

    # --- Mode dispatch ---
    if args.mode == "dd":
        # DD-specific: support/resistance, trend, R/R, LL-01
        s1, s2, r1, r2 = compute_support_resistance(closes, highs, lows)
        trend_label, trend_sentence = analyze_trend(closes)

        entry_price = args.entry_price if args.entry_price else current_price
        stop_price = args.stop
        if stop_price is None and not math.isnan(atr_val):
            stop_price = round(entry_price - atr_1_5x, 2)

        rr = compute_rr(entry_price, args.target, stop_price)
        rr_display = f"{rr:.1f}:1" if not math.isnan(rr) else "N/A"

        gate_reason = ll01_gate_reason(current_price, sma50[-1], sma200[-1], rsi_val, rr=rr)
        confirmations, atr_pass, recommendation, detail = score_ll01(
            closes, opens, volumes, macd_hist, cross_type, cross_bars, atr_pct,
            gate_reason=gate_reason)
        detail_str = ", ".join(f"{k} {'✓' if v else '✗'}" for k, v in detail.items())
        atr_status = "PASS" if atr_pass else "FAIL"
        gate_line = f"\nLL-01 GATE: {gate_reason} — ENTER capped at WATCH" if gate_reason else ""

        output = f"""DUE DILIGENCE: {args.name} ({args.ticker})
PRICE: €{current_price:.2f} (source: {args.source})
RSI(14): {rsi_val:.1f} — [{rsi_zone}] — {rsi_trend}
MACD: line {macd_line}, signal {macd_signal}, histogram {macd_hist} — [{cross_label}]
BOLLINGER: upper {bb_upper}, middle {bb_middle}, lower {bb_lower} — price at {bb_pct:.0f}% — [{bb_zone}]
SMA: 50-day {sma50_val}, 200-day {sma200_val} — [{sma_status} on {sma_cross_date}]
ATR(14): {atr_val} — 1.5× ATR = {atr_1_5x} ({atr_pct}% of price)
VOLUME: {vol_display}
{change_line}
SUPPORT: {s1}, {s2}
RESISTANCE: {r1}, {r2}
TREND: {trend_label} — {trend_sentence}
R/R: {rr_display} (entry {entry_price:.2f} → target {args.target if args.target else 'N/A'} / stop {stop_price if stop_price else 'N/A'})
LL-01: [{confirmations}/4: {detail_str}] — ATR [{atr_status}] — recommendation [{recommendation}]{gate_line}"""
    else:
        # Phase 3: existing P&L + tax computation
        gross_pl = (current_price - args.pru) * args.shares
        gross_pl_pct = (current_price - args.pru) / args.pru * 100

        pea_over_5y = args.pea_years >= 5
        if gross_pl > 0:
            tax_rate = 0.186 if pea_over_5y else 0.314
            net_pl = gross_pl * (1 - tax_rate)
        else:
            net_pl = gross_pl

        pea_age_label = args.pea_age if args.pea_age else (
            f"{'>' if pea_over_5y else '<'}5 years ({args.pea_years:.2f}y)"
        )

        output = f"""POSITION: {args.name} ({args.ticker})
PRICE: €{current_price:.2f} (source: {args.source})
P&L: {gross_pl:+.2f}€ ({gross_pl_pct:+.1f}%)
RSI(14): {rsi_val:.1f} — [{rsi_zone}] — {rsi_trend}
MACD: line {macd_line}, signal {macd_signal}, histogram {macd_hist} — [{cross_label}]
BOLLINGER: upper {bb_upper}, middle {bb_middle}, lower {bb_lower} — price at {bb_pct:.0f}% of band width — [{bb_zone}]
SMA: 50-day {sma50_val}, 200-day {sma200_val} — [{sma_status} on {sma_cross_date}]
ATR(14): {atr_val} — 1.5× ATR = {atr_1_5x} ({atr_pct}% from price)
VOLUME: {vol_display}
{change_line}
TAX (indicative, only on withdrawal): PEA {pea_age_label} — net after tax: {net_pl:+.2f}€"""

    print(output)


if __name__ == "__main__":
    main()
