#!/usr/bin/env python3
"""Assert-based self-check for the pea-manager scripts (stdlib only, no network).

Run: python3 .claude/skills/pea-manager/scripts/selfcheck.py  -> prints OK
"""
import compute_indicators as ci

if __name__ == "__main__":
    # MACD: a linear ramp seeded with an SMA sits at the standard EMA's steady-state
    # lag ((n-1)/2), so line = 12.5 - 5.5 = 7.0 and histogram = 0. Wilder drifts to 14.
    ramp = [float(i) for i in range(1, 121)]
    line, sig, hist, date, kind, since = ci.compute_macd(ramp)
    assert abs(line - 7.0) < 0.01 and abs(hist) < 0.01, (line, hist)
    assert date == "N/A"
    assert ci.compute_macd(ramp[:30])[5] is None  # too short: NaN values, no crossover

    # LL-01 score: each confirmation matches the checklist wording.
    down = [100.0 - i for i in range(40)]                 # RSI 0
    rec = down + [down[-1] + k for k in range(1, 6)]      # 5 up bars: RSI ~31
    vols = [100] * len(rec)
    _, _, _, d = ci.score_ll01(rec, rec, vols, float("nan"), "none", None, 5.0)
    assert d["rsi_recovery"] and d["above_ema5"] and not d["volume_candle"] and not d["macd_cross"], d
    up = [float(i) for i in range(1, 61)]
    assert not ci.score_ll01(up, up, [100] * 60, 0.0, "none", None, 5.0)[3]["rsi_recovery"]
    o = up[:-1] + [up[-1] - 1]                            # last bar green
    v = [100] * 59 + [200]
    assert ci.score_ll01(up, o, v, 0.0, "none", None, 5.0)[3]["volume_candle"]
    assert not ci.score_ll01(up, o, [100] * 59 + [10], 0.0, "none", None, 5.0)[3]["volume_candle"]  # partial bar
    assert ci.score_ll01(up, o, v, 0.5, "bullish", 3, 5.0)[:3] == (3, True, "ENTER")
    assert ci.score_ll01(up, o, v, 0.5, "bullish", 3, 5.0, gate_reason="x")[2] == "WATCH"
    assert ci.score_ll01(up, o, v, 0.5, "bullish", 11, 5.0)[3]["macd_cross"] is False   # stale crossover
    # short history (recent IPO): no raise
    assert ci.score_ll01(up[:10], up[:10], [100] * 10, float("nan"), "none", None, float("nan"))[0:3] == (1, False, "WATCH")

    print("OK")
