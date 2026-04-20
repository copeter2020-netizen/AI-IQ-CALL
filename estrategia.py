import pandas as pd

def calculate_indicators(df):
    df['ema_100'] = df['close'].ewm(span=100).mean()

    ma = df['close'].rolling(14).mean()
    std = df['close'].rolling(14).std()

    df['upper_band'] = ma + 2 * std
    df['lower_band'] = ma - 2 * std

    return df


# ================= BUY =================

def check_buy_signal(df):
    if len(df) < 20:
        return False

    # 🔥 AJUSTE CLAVE DE INDEXACIÓN
    prev = df.iloc[-5]
    c3 = df.iloc[-4]  # impulso
    c4 = df.iloc[-3]
    c5 = df.iloc[-2]

    # 🔥 CRUCE MÁS REALISTA (con tolerancia)
    cross = (
        (c3['upper_band'] - c3['ema_100']) > -0.0001 and
        (prev['upper_band'] - prev['ema_100']) <= 0
    )

    # 🔥 IMPULSO MÁS FLEXIBLE
    impulse = (
        c3['close'] < c3['open'] and
        c3['close'] < c3['ema_100'] and
        c3['close'] <= c3['lower_band'] * 1.02  # más tolerancia
    )

    confirmations = (
        c4['close'] > c4['open'] and
        c5['close'] > c5['open']
    )

    return cross and impulse and confirmations


# ================= SELL =================

def check_sell_signal(df):
    if len(df) < 20:
        return False

    prev = df.iloc[-5]
    c3 = df.iloc[-4]
    c4 = df.iloc[-3]
    c5 = df.iloc[-2]

    cross = (
        (c3['lower_band'] - c3['ema_100']) < 0.0001 and
        (prev['lower_band'] - prev['ema_100']) >= 0
    )

    impulse = (
        c3['close'] > c3['open'] and
        c3['close'] > c3['ema_100'] and
        c3['close'] >= c3['upper_band'] * 0.98
    )

    confirmations = (
        c4['close'] < c4['open'] and
        c5['close'] < c5['open']
    )

    return cross and impulse and confirmations
