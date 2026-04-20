import pandas as pd

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

    prev = df.iloc[-2]     # vela anterior
    signal = df.iloc[-1]   # vela que acaba de cerrar

    # 1. cruce banda inferior sobre EMA 100
    cross = (
        prev['lower_band'] < prev['ema_100'] and
        signal['lower_band'] > signal['ema_100']
    )

    # 2. vela roja
    red_candle = signal['close'] < signal['open']

    # 3. cruce de la media hacia arriba
    mid_cross = (
        signal['open'] < signal['mid_band'] and
        signal['close'] > signal['mid_band']
    )

    if pair:
        print(f"\n📊 {pair} BUY")
        print("CRUCE:", cross)
        print("VELA ROJA:", red_candle)
        print("CRUCE MEDIA:", mid_cross)

    return cross and red_candle and mid_cross


# ================= SELL =================

def check_sell_signal(df, pair=None):
    if len(df) < 20:
        return False

    prev = df.iloc[-2]
    signal = df.iloc[-1]

    # 1. cruce banda superior bajo EMA 100
    cross = (
        prev['upper_band'] > prev['ema_100'] and
        signal['upper_band'] < signal['ema_100']
    )

    # 2. vela verde
    green_candle = signal['close'] > signal['open']

    # 3. cruce de la media hacia abajo
    mid_cross = (
        signal['open'] > signal['mid_band'] and
        signal['close'] < signal['mid_band']
    )

    if pair:
        print(f"\n📊 {pair} SELL")
        print("CRUCE:", cross)
        print("VELA VERDE:", green_candle)
        print("CRUCE MEDIA:", mid_cross)

    return cross and green_candle and mid_cross
