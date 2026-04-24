import pandas as pd

PERIOD = 60

# ================= TII REAL =================

def calculate_tii(df):
    close = df['close']

    # media móvil
    ma = close.rolling(PERIOD).mean()

    # desviación
    dev = close - ma

    # separar positivos y negativos
    pos = dev.copy()
    neg = dev.copy()

    pos[pos < 0] = 0
    neg[neg > 0] = 0

    sum_pos = pos.rolling(PERIOD).sum()
    sum_neg = abs(neg.rolling(PERIOD).sum())

    df['tii'] = 100 * (sum_pos / (sum_pos + sum_neg))

    return df


# ================= DETECCIÓN EN BLOQUE =================

def detect_block_signal(df):
    """
    df: velas de 1 minuto dentro del bloque de 30 min
    """

    df = calculate_tii(df)

    for i in range(1, len(df)):
        prev = df.iloc[i - 1]
        curr = df.iloc[i]

        # 🔥 CALL → cruza 20 hacia arriba
        if prev['tii'] < 20 and curr['tii'] > 20:
            return "call"

        # 🔥 PUT → cruza 80 hacia abajo
        if prev['tii'] > 80 and curr['tii'] < 80:
            return "put"

    return None
