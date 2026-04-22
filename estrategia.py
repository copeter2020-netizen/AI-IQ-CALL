import pandas as pd

LOOKBACK = 20
MIN_BODY = 0.0002

# ================= LIQUIDEZ =================

def get_liquidity_levels(df):
    recent = df.iloc[-LOOKBACK:]
    high = recent['high'].max()
    low = recent['low'].min()
    return high, low

# ================= FUERZA =================

def strong_bullish(c):
    body = c['close'] - c['open']
    rng = c['high'] - c['low']

    return (
        body > MIN_BODY and
        c['close'] > c['open'] and
        c['close'] > (c['high'] - rng * 0.25)
    )

def strong_bearish(c):
    body = c['open'] - c['close']
    rng = c['high'] - c['low']

    return (
        body > MIN_BODY and
        c['close'] < c['open'] and
        c['close'] < (c['low'] + rng * 0.25)
    )

# ================= SETUPS =================

def buy_liquidity_sweep(df):
    high, low = get_liquidity_levels(df)

    prev = df.iloc[-3]
    c = df.iloc[-2]

    return (
        prev['low'] < low and     # rompe liquidez
        c['close'] > low and      # recupera nivel
        strong_bullish(c)         # fuerza alcista
    )

def sell_liquidity_sweep(df):
    high, low = get_liquidity_levels(df)

    prev = df.iloc[-3]
    c = df.iloc[-2]

    return (
        prev['high'] > high and
        c['close'] < high and
        strong_bearish(c)
    )
