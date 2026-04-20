import pandas as pd

# ================= INDICADORES =================

def calculate_indicators(df):
    # EMA 100
    df['ema_100'] = df['close'].ewm(span=100).mean()

    # Bollinger Bands
    ma = df['close'].rolling(14).mean()
    std = df['close'].rolling(14).std()

    df['upper_band'] = ma + 2 * std
    df['lower_band'] = ma - 2 * std
    df['mid_band'] = ma  # línea central

    return df


# ================= BUY =================

def check_buy_signal(df, pair=None):
    if len(df) < 20:
        return False

    # 🔥 vela anterior al cruce
    prev = df.iloc[-3]

    # 🔥 vela donde ocurre la señal (ya cerrada)
    signal = df.iloc[-2]

    # ================= CONDICIONES =================

    # 1. cruce banda inferior sobre EMA 100
    cross = (
        prev['lower_band'] <= prev['ema_100'] and
        signal['lower_band'] > signal['ema_100']
    )

    # 2. ruptura de la media de bollinger
    breakout = signal['close'] > signal['mid_band']

    # ================= DEBUG =================

    if pair:
        print(f"\n📊 {pair} BUY")
        print(f"Lower prev: {prev['lower_band']:.5f} | EMA prev: {prev['ema_100']:.5f}")
        print(f"Lower now: {signal['lower_band']:.5f} | EMA now: {signal['ema_100']:.5f}")
        print(f"Close: {signal['close']:.5f} | Mid: {signal['mid_band']:.5f}")
        print("CRUCE:", cross)
        print("BREAK:", breakout)

    return cross and breakout


# ================= SELL =================

def check_sell_signal(df, pair=None):
    if len(df) < 20:
        return False

    prev = df.iloc[-3]
    signal = df.iloc[-2]

    # 1. cruce banda superior bajo EMA 100
    cross = (
        prev['upper_band'] >= prev['ema_100'] and
        signal['upper_band'] < signal['ema_100']
    )

    # 2. ruptura de la media hacia abajo
    breakout = signal['close'] < signal['mid_band']

    if pair:
        print(f"\n📊 {pair} SELL")
        print(f"Upper prev: {prev['upper_band']:.5f} | EMA prev: {prev['ema_100']:.5f}")
        print(f"Upper now: {signal['upper_band']:.5f} | EMA now: {signal['ema_100']:.5f}")
        print(f"Close: {signal['close']:.5f} | Mid: {signal['mid_band']:.5f}")
        print("CRUCE:", cross)
        print("BREAK:", breakout)

    return cross and breakout
