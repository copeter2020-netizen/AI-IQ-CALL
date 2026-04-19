import pandas as pd

def calculate_indicators(df):
    df['ema_100'] = df['close'].ewm(span=100).mean()

    ma = df['close'].rolling(14).mean()
    std = df['close'].rolling(14).std()

    df['upper_band'] = ma + 2 * std
    df['lower_band'] = ma - 2 * std

    return df

# 🔥 tendencia más flexible pero consistente
def trend_down(df):
    return df['close'].iloc[-1] < df['ema_100'].iloc[-1]

def trend_up(df):
    return df['close'].iloc[-1] > df['ema_100'].iloc[-1]

# 🔥 vela fuerte mejorada
def strong_candle(c):
    body = abs(c['close'] - c['open'])
    total = c['high'] - c['low']
    return body > (total * 0.4)

# 🔥 volatilidad mínima
def valid_volatility(df):
    return (df['high'].iloc[-1] - df['low'].iloc[-1]) > 0

# 🔥 señales más detectables
def check_buy_signal(df):
    if len(df) < 20:
        return False

    c = df.iloc[-1]

    return (
        trend_down(df) and
        valid_volatility(df) and
        c['close'] <= c['lower_band'] and
        strong_candle(c)
    )

def check_sell_signal(df):
    if len(df) < 20:
        return False

    c = df.iloc[-1]

    return (
        trend_up(df) and
        valid_volatility(df) and
        c['close'] >= c['upper_band'] and
        strong_candle(c)
    )
