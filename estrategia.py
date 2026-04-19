import pandas as pd

def calculate_indicators(df):
    df['ema_100'] = df['close'].ewm(span=100).mean()

    ma = df['close'].rolling(window=14).mean()
    std = df['close'].rolling(window=14).std()

    df['upper_band'] = ma + (std * 2)
    df['lower_band'] = ma - (std * 2)

    return df


def check_buy_signal(df):
    if len(df) < 6:
        return False

    prev = df.iloc[-5]
    c3 = df.iloc[-4]
    c4 = df.iloc[-3]
    c5 = df.iloc[-2]

    return (
        c3['close'] < c3['ema_100'] and
        c3['close'] <= c3['lower_band'] and
        c3['close'] < c3['open'] and
        (c3['upper_band'] > c3['ema_100'] and prev['upper_band'] <= prev['ema_100']) and
        c4['close'] > c4['open'] and
        c5['close'] > c5['open']
    )


def check_sell_signal(df):
    if len(df) < 6:
        return False

    prev = df.iloc[-5]
    c3 = df.iloc[-4]
    c4 = df.iloc[-3]
    c5 = df.iloc[-2]

    return (
        c3['close'] > c3['ema_100'] and
        c3['close'] >= c3['upper_band'] and
        c3['close'] > c3['open'] and
        (c3['lower_band'] < c3['ema_100'] and prev['lower_band'] >= prev['ema_100']) and
        c4['close'] < c4['open'] and
        c5['close'] < c5['open']
    )
