import pandas as pd

PERIOD = 60

def calculate_tii(df):
    close = df['close']

    ma = close.rolling(PERIOD).mean()
    dev = close - ma

    pos = dev.copy()
    neg = dev.copy()

    pos[pos < 0] = 0
    neg[neg > 0] = 0

    sum_pos = pos.rolling(PERIOD).sum()
    sum_neg = abs(neg.rolling(PERIOD).sum())

    df['tii'] = 100 * (sum_pos / (sum_pos + sum_neg))

    return df


def detect_signal(df):
    """
    Detecta cruce en últimas velas del bloque
    """

    df = calculate_tii(df)

    # revisar últimas 10 velas (más flexible)
    recent = df.tail(10)

    for i in range(1, len(recent)):
        prev = recent.iloc[i - 1]
        curr = recent.iloc[i]

        # CALL
        if prev['tii'] < 20 and curr['tii'] > 20:
            return "call"

        # PUT
        if prev['tii'] > 80 and curr['tii'] < 80:
            return "put"

    return None
