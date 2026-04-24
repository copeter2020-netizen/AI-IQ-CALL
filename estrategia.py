import pandas as pd

# ================= CONFIG =================

PERIOD = 60  # igual al indicador de tu pantalla

# ================= INDICADOR =================

def calculate_indicators(df):
    # Trend Intensity Index (aproximación fiel)
    close = df['close']

    ma = close.rolling(PERIOD).mean()
    deviation = close - ma

    pos_dev = deviation.copy()
    neg_dev = deviation.copy()

    pos_dev[pos_dev < 0] = 0
    neg_dev[neg_dev > 0] = 0

    sum_pos = pos_dev.rolling(PERIOD).sum()
    sum_neg = abs(neg_dev.rolling(PERIOD).sum())

    df['tii'] = 100 * (sum_pos / (sum_pos + sum_neg))

    return df


# ================= SEÑALES =================

def check_signal(df):
    if len(df) < 100:
        return None

    prev = df.iloc[-3]
    last = df.iloc[-2]

    # ===== CALL (desde zona baja)
    if prev['tii'] < 20 and last['tii'] > 20:
        return "call"

    # ===== PUT (desde zona alta)
    if prev['tii'] > 80 and last['tii'] < 80:
        return "put"

    return None
