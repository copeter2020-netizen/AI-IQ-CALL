import pandas as pd

LOOKBACK = 20
MIN_BODY = 0.00015

# ================= LIQUIDEZ =================

def get_levels(df):
    recent = df.iloc[-LOOKBACK:]
    return recent['high'].max(), recent['low'].min()

# ================= FUERZA =================

def bullish_strength(c):
    body = c['close'] - c['open']
    rng = c['high'] - c['low']
    return body > MIN_BODY and c['close'] > (c['high'] - rng * 0.3)

def bearish_strength(c):
    body = c['open'] - c['close']
    rng = c['high'] - c['low']
    return body > MIN_BODY and c['close'] < (c['low'] + rng * 0.3)

# ================= 1. LIQUIDITY SWEEP =================

def buy_sweep(df):
    high, low = get_levels(df)
    prev = df.iloc[-3]
    c = df.iloc[-2]

    return prev['low'] < low and c['close'] > low and bullish_strength(c)

def sell_sweep(df):
    high, low = get_levels(df)
    prev = df.iloc[-3]
    c = df.iloc[-2]

    return prev['high'] > high and c['close'] < high and bearish_strength(c)

# ================= 2. REBOTE EN SOPORTE / RESISTENCIA =================

def buy_rejection(df):
    high, low = get_levels(df)
    c = df.iloc[-2]

    return (
        abs(c['low'] - low) < 0.0003 and
        c['close'] > c['open']
    )

def sell_rejection(df):
    high, low = get_levels(df)
    c = df.iloc[-2]

    return (
        abs(c['high'] - high) < 0.0003 and
        c['close'] < c['open']
    )

# ================= 3. CONTINUIDAD =================

def buy_continuation(df):
    c = df.iloc[-2]
    prev = df.iloc[-3]

    return (
        c['close'] > c['open'] and
        prev['close'] > prev['open'] and
        c['close'] > prev['close']
    )

def sell_continuation(df):
    c = df.iloc[-2]
    prev = df.iloc[-3]

    return (
        c['close'] < c['open'] and
        prev['close'] < prev['open'] and
        c['close'] < prev['close']
    )

# ================= MASTER SIGNAL =================

def get_signal(df):
    if buy_sweep(df) or buy_rejection(df) or buy_continuation(df):
        return "call"

    if sell_sweep(df) or sell_rejection(df) or sell_continuation(df):
        return "put"

    return None
