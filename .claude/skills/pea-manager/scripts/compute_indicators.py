#!/usr/bin/env python3
"""
Compute technical indicators from OHLCV data for PEA portfolio positions.

Usage:
  python3 compute_indicators.py \
    --name "Air Liquide" --ticker "AI.PA" \
    --shares 44 --pru 139.755 --pea-age ">5" --source "yfinance" \
    < ohlcv.json

Input (stdin): JSON object with parallel arrays:
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

def compute_rsi(closes, period=14):
    """Wilder's smoothed RSI. Returns (rsi_value, trend).

    trend is 'rising' | 'falling' | 'stable' based on last 5 RSI values.
    """
    if len(closes) < period + 1:
        return float("nan"), "stable"

    deltas = [closes[i] - closes[i - 1] for i in range(1, len(closes))]
    gains = [max(d, 0) for d in deltas]
    losses = [abs(min(d, 0)) for d in deltas]

    # Seed: simple average of first `period` gains/losses
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period

    rsi_values = []
    if avg_loss == 0:
        rsi_values.append(100.0)
    else:
        rs = avg_gain / avg_loss
        rsi_values.append(100.0 - (100.0 / (1.0 + rs)))

    # Wilder's smoothing for remaining values
    for i in range(period, len(gains)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
        if avg_loss == 0:
            rsi_values.append(100.0)
        else:
            rs = avg_gain / avg_loss
            rsi_values.append(100.0 - (100.0 / (1.0 + rs)))

    # Determine trend from last 5 RSI values (or fewer if not enough)
    recent = rsi_values[-min(5, len(rsi_values)):]
    if len(recent) >= 2:
        if recent[-1] > recent[0] + 2:
            trend = "rising"
        elif recent[-1] < recent[0] - 2:
            trend = "falling"
        else:
            trend = "stable"
    else:
        trend = "stable"

    return round(rsi_values[-1], 1), trend


def compute_macd(closes, fast=12, slow=26, signal=9):
    """MACD: EMA_fast - EMA_slow, signal line, histogram.

    Returns (macd_line, signal_line, histogram, crossover_date, crossover_type).

    crossover_type is 'bullish' | 'bearish' | 'none'.
    crossover_date is the date string or 'N/A'.
    """
    if len(closes) < slow + signal:
        return float("nan"), float("nan"), float("nan"), "N/A", "none"

    ema_fast = ema(closes, fast)
    ema_slow = ema(closes, slow)

    # MACD line = fast EMA - slow EMA
    macd_line_series = []
    for i in range(len(closes)):
        if math.isnan(ema_fast[i]) or math.isnan(ema_slow[i]):
            macd_line_series.append(float("nan"))
        else:
            macd_line_series.append(ema_fast[i] - ema_slow[i])

    # Signal line = EMA(signal) of MACD line
    # Find first valid MACD index
    valid_start = next((i for i, v in enumerate(macd_line_series) if not math.isnan(v)), 0)
    valid_macd = macd_line_series[valid_start:]
    signal_series_raw = ema(valid_macd, signal)

    # Re-align: pad with NaN at the beginning
    signal_series = [float("nan")] * (valid_start + signal - 1)
    signal_series += signal_series_raw[signal - 1:]

    # Find most recent crossover
    crossover_date = "N/A"
    crossover_type = "none"
    for i in range(1, len(closes)):
        prev_m = macd_line_series[i - 1]
        prev_s = signal_series[i - 1] if i - 1 < len(signal_series) else float("nan")
        curr_m = macd_line_series[i]
        curr_s = signal_series[i] if i < len(signal_series) else float("nan")
        if math.isnan(prev_m) or math.isnan(prev_s) or math.isnan(curr_m) or math.isnan(curr_s):
            continue
        if prev_m <= prev_s and curr_m > curr_s:
            crossover_type = "bullish"
            crossover_date = dates[i] if i < len(dates) else "N/A"
        elif prev_m >= prev_s and curr_m < curr_s:
            crossover_type = "bearish"
            crossover_date = dates[i] if i < len(dates) else "N/A"

    current_macd = macd_line_series[-1] if not math.isnan(macd_line_series[-1]) else float("nan")
    current_signal = signal_series[-1] if len(signal_series) > 0 and not (math.isnan(signal_series[-1]) if len(signal_series) > 0 else True) else float("nan")
    histogram = (current_macd - current_signal) if not (math.isnan(current_macd) or math.isnan(current_signal)) else float("nan")

    return (round(current_macd, 2) if not math.isnan(current_macd) else float("nan"),
            round(current_signal, 2) if not (math.isnan(current_signal)) else float("nan"),
            round(histogram, 2) if not (math.isnan(histogram) if isinstance(histogram, float) else False) else float("nan"),
            crossover_date,
            crossover_type)


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
    Returns (s1, s1_label, s2, s2_label, r1, r1_label, r2, r2_label).
    Labels describe zone strength: 'strong' | 'moderate' | 'weak'."""
    if len(closes) < 20:
        return "N/A", "N/A", "N/A", "N/A", "N/A", "N/A", "N/A", "N/A"

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


def score_ll01(rsi_val, macd_hist, vol_ratio, bb_pct, atr_pct, entry_price):
    """Automate LL-01 technical confirmation scoring.
    Returns (confirmations, atr_pass, recommendation).
    confirmation is int 0-4, atr_pass is bool, recommendation is
    'ENTER' | 'WATCH' | 'SKIP'."""
    confirmations = 0

    # 1. RSI crossing above 30 (or already above 30 and rising)
    if rsi_val is None or math.isnan(rsi_val):
        pass  # can't score
    elif rsi_val >= 35:  # conservative: above oversold
        confirmations += 1

    # 2. MACD bullish (histogram positive = line above signal)
    if macd_hist is None or math.isnan(macd_hist):
        pass
    elif macd_hist > 0:
        confirmations += 1

    # 3. Volume > 1.5x 20d avg
    if vol_ratio is None or math.isnan(vol_ratio):
        pass
    elif vol_ratio > 50:  # 50% above average
        confirmations += 1

    # 4. Price closing above SMA5 (approximated by BB middle for now)
    if bb_pct is None or math.isnan(bb_pct):
        pass
    elif bb_pct >= 40:  # above lower-middle of BB
        confirmations += 1

    # ATR check: 1.5x ATR must be <= 10% of entry price
    atr_pass = atr_pct is not None and not math.isnan(atr_pct) and atr_pct <= 10.0

    # Recommendation tier
    if confirmations >= 3 and atr_pass:
        recommendation = "ENTER"
    elif confirmations >= 1:
        recommendation = "WATCH"
    else:
        recommendation = "SKIP"

    return confirmations, atr_pass, recommendation


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
    parser.add_argument("--pea-age", default="",
                        help='PEA age, e.g. ">5 years" (phase3 only)')
    parser.add_argument("--source", default="yfinance", help="Data source name (yfinance/eodhd)")
    parser.add_argument("--entry-price", type=float, default=None,
                        help="Planned entry price in EUR (dd mode)")
    parser.add_argument("--target", type=float, default=None,
                        help="Profit target price in EUR (dd mode)")
    parser.add_argument("--stop", type=float, default=None,
                        help="Stop loss price in EUR (dd mode, auto-computed from ATR if omitted)")
    parser.add_argument("--input", "-i", default=None, help="Path to JSON input file (default: stdin)")
    args = parser.parse_args()

    # Validate mode-specific requirements
    if args.mode == "phase3":
        if args.shares <= 0:
            print("ERROR: --shares required for phase3 mode", file=sys.stderr)
            sys.exit(1)
        if args.pru <= 0:
            print("ERROR: --pru required for phase3 mode", file=sys.stderr)
            sys.exit(1)
        if not args.pea_age:
            print("ERROR: --pea-age required for phase3 mode", file=sys.stderr)
            sys.exit(1)

    # Read input
    if args.input:
        with open(args.input, "r") as f:
            data = json.load(f)
    else:
        data = json.load(sys.stdin)

    # Unpack OHLCV arrays
    global dates  # used by macd crossover detection
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

    macd_line, macd_signal, macd_hist, cross_date, cross_type = compute_macd(closes)
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
    sma50_val = sma50[-1] if not math.isnan(sma50[-1]) else "N/A"
    sma200_val = sma200[-1] if not math.isnan(sma200[-1]) else "N/A"

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

        # LL-01 scoring
        # vol_ratio for LL-01: use vol_pct_diff which is recent vs 20d % change
        vol_ratio_for_ll01 = vol_pct_diff if not math.isnan(vol_pct_diff) else 0
        confirmations, atr_pass, recommendation = score_ll01(
            rsi_val, macd_hist, vol_ratio_for_ll01, bb_pct, atr_pct, entry_price
        )
        atr_status = "PASS" if atr_pass else "FAIL"

        output = f"""DUE DILIGENCE: {args.name} ({args.ticker})
PRICE: €{current_price:.2f} (source: {args.source})
RSI(14): {rsi_val:.1f} — [{rsi_zone}] — {rsi_trend}
MACD: line {macd_line}, signal {macd_signal}, histogram {macd_hist} — [{cross_label}]
BOLLINGER: upper {bb_upper}, middle {bb_middle}, lower {bb_lower} — price at {bb_pct:.0f}% — [{bb_zone}]
SMA: 50-day {sma50_val}, 200-day {sma200_val} — [{sma_status} on {sma_cross_date}]
ATR(14): {atr_val} — 1.5× ATR = {atr_1_5x} ({atr_pct}% of price)
VOLUME: {vol_display}
SUPPORT: {s1}, {s2}
RESISTANCE: {r1}, {r2}
TREND: {trend_label} — {trend_sentence}
R/R: {rr_display} (entry {entry_price:.2f} → target {args.target if args.target else 'N/A'} / stop {stop_price if stop_price else 'N/A'})
LL-01: [{confirmations}/4 confirmations] — ATR [{atr_status}] — recommendation [{recommendation}]"""
    else:
        # Phase 3: existing P&L + tax computation
        gross_pl = (current_price - args.pru) * args.shares
        gross_pl_pct = (current_price - args.pru) / args.pru * 100

        if ">" in args.pea_age or ("5" in args.pea_age and ">" in args.pea_age):
            if gross_pl > 0:
                tax_rate = 0.172
                net_pl = gross_pl * (1 - tax_rate)
            else:
                net_pl = gross_pl
        else:
            if gross_pl > 0:
                tax_rate = 0.30
                net_pl = gross_pl * (1 - tax_rate)
            else:
                net_pl = gross_pl

        output = f"""POSITION: {args.name} ({args.ticker})
PRICE: €{current_price:.2f} (source: {args.source})
P&L: {gross_pl:+.2f}€ ({gross_pl_pct:+.1f}%)
RSI(14): {rsi_val:.1f} — [{rsi_zone}] — {rsi_trend}
MACD: line {macd_line}, signal {macd_signal}, histogram {macd_hist} — [{cross_label}]
BOLLINGER: upper {bb_upper}, middle {bb_middle}, lower {bb_lower} — price at {bb_pct:.0f}% of band width — [{bb_zone}]
SMA: 50-day {sma50_val}, 200-day {sma200_val} — [{sma_status} on {sma_cross_date}]
ATR(14): {atr_val} — 1.5× ATR = {atr_1_5x} ({atr_pct}% from price)
VOLUME: {vol_display}
TAX: PEA {args.pea_age} — net after tax: {net_pl:+.2f}€"""

    print(output)


if __name__ == "__main__":
    main()
