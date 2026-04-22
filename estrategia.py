import pandas as pd

# ================= CONFIG =================

EMA_PERIOD = 50
MIN_BODY = 0.0002
MIN_RANGE = 0.0005

# ================= INDICADORES =================

def apply_indicators(df):
    df['ema'] = df['close'].ewm(span=EMA_PERIOD).mean()
    df['ema_slope'] = df['ema'].diff()
    return df

# ================= TENDENCIA =================

def trend(df):
    slope = df['ema_slope'].iloc[-2]

    if slope > 0:
        return "up"
    elif slope < 0:
        return "down"
    return "range"

# ================= FILTRO DE FUERZA =================

def strong_bullish(c):
    body = c['close'] - c['open']
    rng = c['high'] - c['low']

    return (
        body > MIN_BODY and
        rng > MIN_RANGE and
        c['close'] > c['open'] and
        c['close'] > (c['high'] - rng * 0.2)
    )

def strong_bearish(c):
    body = c['open'] - c['close']
    rng = c['high'] - c['low']

    return (
        body > MIN_BODY and
        rng > MIN_RANGE and
        c['close'] < c['open'] and
        c['close'] < (c['low'] + rng * 0.2)
    )

# ================= EVITAR AGOTAMIENTO =================

def not_exhausted(prev, c):
    prev_range = prev['high'] - prev['low']
    curr_range = c['high'] - c['low']

    return curr_range < prev_range * 1.8  # evita velas explosivas tardías
