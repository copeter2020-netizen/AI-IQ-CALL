import time


def smart_entry(iq, pair, action):

    start = time.time()

    while time.time() - start < 5:

        try:

            candles = iq.get_candles(pair, 60, 2, time.time())

            last = candles[-1]

            price = last["close"]

            open_price = last["open"]

            if action == "call":

                if price < open_price:
                    return True

            if action == "put":

                if price > open_price:
                    return True

        except:
            pass

        time.sleep(0.3)

    return True
