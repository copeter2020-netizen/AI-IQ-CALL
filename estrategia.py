import pandas as pd

# ================= CONFIG =================

MIN_BODY_RATIO = 0.6
MAX_WICK_RATIO = 0.3

# ================= CONTINUIDAD =================

def bullish_confirmation(c):
    body = c['close'] - c['open']
    total = c['high'] - c['low']

    if total == 0:
        return False

    upper_wick = c['high'] - c['close']

    return (
        body > 0 and
        body > total * MIN_BODY_RATIO and
        upper_wick < body * MAX_WICK_RATIO and
        c['close'] >= c['high'] - (total * 0.2)
    )


def bearish_confirmation(c):
    body = c['open'] - c['close']
    total = c['high'] - c['low']

    if total == 0:
        return False

    lower_wick = c['close'] - c['low']

    return (
        body > 0 and
        body > total * MIN_BODY_RATIO and
        lower_wick < body * MAX_WICK_RATIO and
        c['close'] <= c['low'] + (total * 0.2)
    )
