from iqoptionapi.stable_api import IQ_Option
import time

EMAIL = "TU_EMAIL"
PASSWORD = "TU_PASSWORD"

API = IQ_Option(EMAIL, PASSWORD)
API.connect()

PARES = ["EURUSD", "GBPUSD", "GBPJPY", "USDCHF", "EURJPY", "EURGBP"]


def obtener_datos():

    data = {}

    for par in PARES:
        velas = API.get_candles(par, 60, 50, time.time())

        data[par] = []

        for v in velas:
            data[par].append({
                "open": v["open"],
                "close": v["close"],
                "max": v["max"],
                "min": v["min"]
            })

    return data
