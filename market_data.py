import time


def get_candles(iq, pair, timeframe=60, count=50):

    try:

        candles = iq.get_candles(pair, timeframe, count, time.time())

        return candles

    except Exception as e:

        print("Error obteniendo velas:", e)

        return []
