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

    # 🔥 velas exactas (todas cerradas)
    prev = df.iloc[-6]
    c3 = df.iloc[-5]  # impulso roja
    c4 = df.iloc[-4]  # confirmación 1
    c5 = df.iloc[-3]  # confirmación 2

    # 🔥 CRUCE REAL
    cross = (
        prev['upper_band'] <= prev['ema_100'] and
        c3['upper_band'] > c3['ema_100']
    )

    # 🔴 impulso correcto
    impulse = (
        c3['close'] < c3['open'] and  # roja
        c3['close'] < c3['ema_100'] and  # debajo EMA
        c3['close'] <= c3['lower_band'] * 1.01  # cerca banda inferior (tolerancia)
    )

    # 🟢 confirmaciones
    confirmations = (
        c4['close'] > c4['open'] and
        c5['close'] > c5['open']
    )

    return cross and impulse and confirmations


# ================= SELL =================

def check_sell_signal(df):
    if len(df) < 20:
        return False

    prev = df.iloc[-6]
    c3 = df.iloc[-5]
    c4 = df.iloc[-4]
    c5 = df.iloc[-3]

    # 🔥 CRUCE REAL
    cross = (
        prev['lower_band'] >= prev['ema_100'] and
        c3['lower_band'] < c3['ema_100']
    )

    # 🟢 impulso correcto
    impulse = (
        c3['close'] > c3['open'] and
        c3['close'] > c3['ema_100'] and
        c3['close'] >= c3['upper_band'] * 0.99
    )

    # 🔴 confirmaciones
    confirmations = (
        c4['close'] < c4['open'] and
        c5['close'] < c5['open']
    )

    return cross and impulse and confirmations
