import pandas as pd

# ================= CONFIG =================

LOOKBACK = 25
ZONE_TOL = 0.0004
PRE_TOL = 0.0008


# ================= INDICADORES =================

def calculate_indicators(df):
    df['ema_50'] = df['close'].ewm(span=50).mean()
    df['ema_100'] = df['close'].ewm(span=100).mean()
    df['ema_slope'] = df['ema_50'].diff()
    return df


# ================= ESTRUCTURA =================

def get_support_resistance(df):
    recent = df.iloc[-LOOKBACK:]
    support = recent['low'].min()
    resistance = recent['high'].max()
    return support, resistance


# ================= TENDENCIA =================

def get_trend(df):
    slope = df['ema_slope'].iloc[-2]

    if slope > 0:
        return "up"
    elif slope < 0:
        return "down"
    return "range"


# ================= RECHAZOS =================

def bullish_rejection(c, level):
    return (
        c['low'] <= level + ZONE_TOL and
        c['close'] > c['open']
    )


def bearish_rejection(c, level):
    return (
        c['high'] >= level - ZONE_TOL and
        c['close'] < c['open']
    )


def close_near_level(c, level):
    return abs(c['close'] - level) <= ZONE_TOL


# ================= PRE-SEÑAL =================

def pre_buy(df):
    c = df.iloc[-1]
    support, _ = get_support_resistance(df)

    return (
        c['low'] <= support + PRE_TOL and
        c['close'] > c['open']
    )


def pre_sell(df):
    c = df.iloc[-1]
    _, resistance = get_support_resistance(df)

    return (
        c['high'] >= resistance - PRE_TOL and
        c['close'] < c['open']
    )


# ================= CONFIRMACIÓN =================

def confirm_buy(df):
    if len(df) < 50:
        return False

    c = df.iloc[-2]
    support, _ = get_support_resistance(df)
    trend = get_trend(df)

    return (
        trend != "down" and
        (bullish_rejection(c, support) or close_near_level(c, support))
    )


def confirm_sell(df):
    if len(df) < 50:
        return False

    c = df.iloc[-2]
    _, resistance = get_support_resistance(df)
    trend = get_trend(df)

    return (
        trend != "up" and
        (bearish_rejection(c, resistance) or close_near_level(c, resistance))
    )
