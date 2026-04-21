import pandas as pd

# ================= CONFIG =================

LOOKBACK = 25
ZONE_TOL = 0.0004
PRE_TOL = 0.0008  # tolerancia de anticipación

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


# ================= PRE-SEÑAL (INTRAVELA) =================

def pre_buy(df):
    c = df.iloc[-1]  # vela en formación
    support, _ = get_support_resistance(df)

    return (
        c['low'] <= support + PRE_TOL
    )


def pre_sell(df):
    c = df.iloc[-1]
    _, resistance = get_support_resistance(df)

    return (
        c['high'] >= resistance - PRE_TOL
    )


# ================= CONFIRMACIÓN (CIERRE) =================

def confirm_buy(df):
    if len(df) < 50:
        return False

    c = df.iloc[-2]
    support, _ = get_support_resistance(df)

    trend = get_trend(df)

    return (
        trend != "down" and
        c['close'] > c['open'] and
        abs(c['close'] - support) <= ZONE_TOL
    )


def confirm_sell(df):
    if len(df) < 50:
        return False

    c = df.iloc[-2]
    _, resistance = get_support_resistance(df)

    trend = get_trend(df)

    return (
        trend != "up" and
        c['close'] < c['open'] and
        abs(c['close'] - resistance) <= ZONE_TOL
    )
