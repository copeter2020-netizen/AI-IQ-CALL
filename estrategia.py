import pandas as pd
import numpy as np

# ===============================
# 🔥 CALCULAR INDICADOR TII
# ===============================

def calculate_indicators(df):

    # Media
    period = 20
    df['ma'] = df['close'].rolling(period).mean()

    # Diferencia vs media
    df['diff'] = df['close'] - df['ma']

    # Separar positivos y negativos
    df['pos'] = df['diff'].apply(lambda x: x if x > 0 else 0)
    df['neg'] = df['diff'].apply(lambda x: abs(x) if x < 0 else 0)

    # Sumas
    df['sum_pos'] = df['pos'].rolling(period).sum()
    df['sum_neg'] = df['neg'].rolling(period).sum()

    # TII (0 - 100)
    df['tii'] = 100 * (df['sum_pos'] / (df['sum_pos'] + df['sum_neg']))

    return df


# ===============================
# 🔥 GENERAR SEÑALES
# ===============================

def check_signal(df):

    if len(df) < 30:
        return None

    last = df.iloc[-1]
    prev = df.iloc[-2]

    tii_now = last['tii']
    tii_prev = prev['tii']

    price_now = last['close']
    price_prev = prev['close']

    # ===============================
    # 🔥 COMPRA (CALL)
    # Cruce de abajo hacia arriba del 20
    # ===============================
    if tii_prev < 20 and tii_now > 20:
        return "call"

    # ===============================
    # 🔥 VENTA (PUT)
    # Cruce de arriba hacia abajo del 80
    # ===============================
    if tii_prev > 80 and tii_now < 80:
        return "put"

    return None
