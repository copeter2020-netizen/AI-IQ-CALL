import pandas as pd

def calculate_indicators(df):
    df['ema_100'] = df['close'].ewm(span=100).mean()

    df['ma'] = df['close'].rolling(window=14).mean()
    df['std'] = df['close'].rolling(window=14).std()

    df['upper_band'] = df['ma'] + (df['std'] * 2)
    df['lower_band'] = df['ma'] - (df['std'] * 2)

    return df


def check_buy_signal(df):
    if len(df) < 6:
        return False

    c3 = df.iloc[-4]
    c4 = df.iloc[-3]
    c5 = df.iloc[-2]
    c6 = df.iloc[-1]

    cond_trend = c3['close'] < c3['ema_100']
    cond_band = c3['close'] <= c3['lower_band'] * 1.01
    cond_red = c3['close'] < c3['open']

    cross = (c4['upper_band'] > c4['ema_100']) and (c3['upper_band'] <= c3['ema_100'])

    green1 = c5['close'] > c5['open']
    green2 = c6['close'] > c6['open']

    return cond_trend and cond_band and cond_red and cross and green1 and green2


def check_sell_signal(df):
    if len(df) < 6:
        return False

    c3 = df.iloc[-4]
    c4 = df.iloc[-3]
    c5 = df.iloc[-2]
    c6 = df.iloc[-1]

    cond_trend = c3['close'] > c3['ema_100']
    cond_band = c3['close'] >= c3['upper_band'] * 0.99
    cond_green = c3['close'] > c3['open']

    cross = (c4['lower_band'] < c4['ema_100']) and (c3['lower_band'] >= c3['ema_100'])

    red1 = c5['close'] < c5['open']
    red2 = c6['close'] < c6['open']

    return cond_trend and cond_band and cond_green and cross and red1 and red2
