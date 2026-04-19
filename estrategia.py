import pandas as pd

def calculate_indicators(df):
    # EMA 100
    df['ema_100'] = df['close'].ewm(span=100).mean()

    # Bollinger Bands (14, 2)
    df['ma'] = df['close'].rolling(window=14).mean()
    df['std'] = df['close'].rolling(window=14).std()

    df['upper_band'] = df['ma'] + (df['std'] * 2)
    df['lower_band'] = df['ma'] - (df['std'] * 2)

    return df


def check_buy_signal(df):
    if len(df) < 6:
        return False

    c1 = df.iloc[-6]
    c2 = df.iloc[-5]
    c3 = df.iloc[-4]
    c4 = df.iloc[-3]
    c5 = df.iloc[-2]
    c6 = df.iloc[-1]

    # Precio por debajo de EMA 100
    cond_trend = c3['close'] < c3['ema_100']

    # Precio cerca o tocando banda inferior
    cond_band = c3['close'] <= c3['lower_band'] * 1.01

    # Vela roja
    cond_red = c3['close'] < c3['open']

    # Cruce banda superior sobre EMA 100
    cross = (c4['upper_band'] > c4['ema_100']) and (c3['upper_band'] <= c3['ema_100'])

    # Dos velas verdes
    green1 = c5['close'] > c5['open']
    green2 = c6['close'] > c6['open']

    if cond_trend and cond_band and cond_red and cross and green1 and green2:
        return True

    return False


def check_sell_signal(df):
    if len(df) < 6:
        return False

    c1 = df.iloc[-6]
    c2 = df.iloc[-5]
    c3 = df.iloc[-4]
    c4 = df.iloc[-3]
    c5 = df.iloc[-2]
    c6 = df.iloc[-1]

    # Precio por encima de EMA 100
    cond_trend = c3['close'] > c3['ema_100']

    # Precio cerca o tocando banda superior
    cond_band = c3['close'] >= c3['upper_band'] * 0.99

    # Vela verde
    cond_green = c3['close'] > c3['open']

    # Cruce banda inferior bajo EMA 100
    cross = (c4['lower_band'] < c4['ema_100']) and (c3['lower_band'] >= c3['ema_100'])

    # Dos velas rojas
    red1 = c5['close'] < c5['open']
    red2 = c6['close'] < c6['open']

    if cond_trend and cond_band and cond_green and cross and red1 and red2:
        return True

    return False
