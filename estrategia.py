import pandas as pd

# ================= CONFIG =================

LOOKBACK = 25
ZONE_TOL = 0.0006     # 🔥 ampliado para permitir entradas reales
PRE_TOL = 0.0010      # 🔥 anticipación más flexible


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


# ================= CONFIRMACIÓN (MEJORADA) =================

def confirm_buy(df):
    if len(df) < 50:
        return False

    c = df.iloc[-2]
    support, _ = get_support_resistance(df)

    # 🔥 zona más flexible
    near_zone = abs(c['low'] - support) <= ZONE_TOL * 2

    # 🔥 rechazo más realista
    rejection = (
        c['close'] > c['open'] or
        c['close'] > support
    )

    return (
        get_trend(df) != "down" and
        near_zone and
        rejection
    )


def confirm_sell(df):
    if len(df) < 50:
        return False

    c = df.iloc[-2]
    _, resistance = get_support_resistance(df)

    near_zone = abs(c['high'] - resistance) <= ZONE_TOL * 2

    rejection = (
        c['close'] < c['open'] or
        c['close'] < resistance
    )

    return (
        get_trend(df) != "up" and
        near_zone and
        rejection
    )
