import pandas as pd

# ================= INDICADORES =================

def calculate_indicators(df):
    df['ema_100'] = df['close'].ewm(span=100).mean()

    ma = df['close'].rolling(window=14).mean()
    std = df['close'].rolling(window=14).std()

    df['upper_band'] = ma + (std * 2)
    df['lower_band'] = ma - (std * 2)

    return df

# ================= FILTROS =================

def trend_down(df):
    return (
        df['close'].iloc[-2] < df['ema_100'].iloc[-2] and
        df['close'].iloc[-3] < df['ema_100'].iloc[-3] and
        df['close'].iloc[-4] < df['ema_100'].iloc[-4]
    )

def trend_up(df):
    return (
        df['close'].iloc[-2] > df['ema_100'].iloc[-2] and
        df['close'].iloc[-3] > df['ema_100'].iloc[-3] and
        df['close'].iloc[-4] > df['ema_100'].iloc[-4]
    )

def strong_bullish(candle):
    body = abs(candle['close'] - candle['open'])
    wick = candle['high'] - candle['low']
    return body > (wick * 0.5)

def strong_bearish(candle):
    body = abs(candle['close'] - candle['open'])
    wick = candle['high'] - candle['low']
    return body > (wick * 0.5)

def valid_volatility(df):
    last_range = df['high'].iloc[-2] - df['low'].iloc[-2]
    avg_range = (df['high'] - df['low']).rolling(10).mean().iloc[-2]

    return last_range > avg_range * 0.7

def recent_cross_up(df):
    return (
        df['lower_band'].iloc[-4] < df['ema_100'].iloc[-4] or
        df['lower_band'].iloc[-3] < df['ema_100'].iloc[-3]
    )

def recent_cross_down(df):
    return (
        df['upper_band'].iloc[-4] > df['ema_100'].iloc[-4] or
        df['upper_band'].iloc[-3] > df['ema_100'].iloc[-3]
    )

# ================= SEÑALES =================

def check_buy_signal(df):
    if len(df) < 20:
        return False

    c2 = df.iloc[-2]

    return (
        trend_down(df) and
        valid_volatility(df) and
        c2['close'] <= c2['lower_band'] and
        strong_bullish(c2) and
        recent_cross_up(df)
    )

def check_sell_signal(df):
    if len(df) < 20:
        return False

    c2 = df.iloc[-2]

    return (
        trend_up(df) and
        valid_volatility(df) and
        c2['close'] >= c2['upper_band'] and
        strong_bearish(c2) and
        recent_cross_down(df)
    )
