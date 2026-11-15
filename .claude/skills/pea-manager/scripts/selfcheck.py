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

    print("OK")
