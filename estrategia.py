import pandas as pd

TOL = 0.0003  # tolerancia visual

# ================= INDICADORES =================

def calculate_indicators(df):
    df['ema_100'] = df['close'].ewm(span=100).mean()

    ma = df['close'].rolling(14).mean()
    std = df['close'].rolling(14).std()

    df['upper_band'] = ma + 2 * std
    df['lower_band'] = ma - 2 * std
    df['mid_band'] = ma

    return df


# ================= BUY =================

def check_buy_signal(df, pair=None):
    if len(df) < 20:
        return False

    signal = df.iloc[-1]

    # 🔥 CRUCE VISUAL (con tolerancia + mecha)
    cross = (
        signal['lower_band'] > signal['ema_100'] or
        abs(signal['lower_band'] - signal['ema_100']) < TOL or
        signal['low'] < signal['ema_100']
    )

    # vela roja
    red = signal['close'] < signal['open']

    # 🔥 ruptura visual de media (cuerpo o mecha)
    mid_break = (
        signal['close'] > signal['mid_band'] or
        signal['high'] > signal['mid_band']
    )

    if pair:
        print(f"\n📊 {pair} BUY")
        print("CRUCE:", cross)
        print("ROJA:", red)
        print("MEDIA:", mid_break)

    return cross and red and mid_break


# ================= SELL =================

def check_sell_signal(df, pair=None):
    if len(df) < 20:
        return False

    signal = df.iloc[-1]

    # 🔥 CRUCE VISUAL
    cross = (
        signal['upper_band'] < signal['ema_100'] or
        abs(signal['upper_band'] - signal['ema_100']) < TOL or
        signal['high'] > signal['ema_100']
    )

    # vela verde
    green = signal['close'] > signal['open']

    # 🔥 ruptura visual de media
    mid_break = (
        signal['close'] < signal['mid_band'] or
        signal['low'] < signal['mid_band']
    )

    if pair:
        print(f"\n📊 {pair} SELL")
        print("CRUCE:", cross)
        print("VERDE:", green)
        print("MEDIA:", mid_break)

    return cross and green and mid_break
