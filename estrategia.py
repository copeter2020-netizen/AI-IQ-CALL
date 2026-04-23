import pandas as pd

LOOKBACK = 20
ZONE_TOL = 0.0003
MIN_BODY = 0.00015

# ================= ZONAS =================

def get_zones(df):
    recent = df.iloc[-LOOKBACK:]
    resistance = recent['high'].max()
    support = recent['low'].min()
    return resistance, support

def in_resistance(price, resistance):
    return abs(price - resistance) < ZONE_TOL

def in_support(price, support):
    return abs(price - support) < ZONE_TOL

# ================= FUERZA =================

def bullish(c):
    body = c['close'] - c['open']
    return body > MIN_BODY and c['close'] > c['open']

def bearish(c):
    body = c['open'] - c['close']
    return body > MIN_BODY and c['close'] < c['open']

# ================= RECHAZO =================

def rejection_buy(df):
    res, sup = get_zones(df)
    c = df.iloc[-2]

    return in_support(c['low'], sup) and bullish(c)

def rejection_sell(df):
    res, sup = get_zones(df)
    c = df.iloc[-2]

    return in_resistance(c['high'], res) and bearish(c)

# ================= RUPTURA =================

def breakout_up(df):
    res, sup = get_zones(df)
    c = df.iloc[-2]
    prev = df.iloc[-3]

    return prev['close'] < res and c['close'] > res

def breakout_down(df):
    res, sup = get_zones(df)
    c = df.iloc[-2]
    prev = df.iloc[-3]

    return prev['close'] > sup and c['close'] < sup

# ================= CONFIRMACIÓN =================

def continuation_buy(df):
    c = df.iloc[-2]
    prev = df.iloc[-3]

    return bullish(c) and c['close'] > prev['close']

def continuation_sell(df):
    c = df.iloc[-2]
    prev = df.iloc[-3]

    return bearish(c) and c['close'] < prev['close']

# ================= FILTRO CENTRAL =================

def get_signal(df):

    # 🔥 1. RECHAZO EN ZONA
    if rejection_buy(df):
        return "call"

    if rejection_sell(df):
        return "put"

    # 🔥 2. RUPTURA + CONFIRMACIÓN
    if breakout_up(df) and continuation_buy(df):
        return "call"

    if breakout_down(df) and continuation_sell(df):
        return "put"

    return None
