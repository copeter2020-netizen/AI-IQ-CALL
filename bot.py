import requests
import time
from iqoptionapi.stable_api import IQ_Option
from strategy import detectar_entrada

EMAIL = "TU_EMAIL"
PASSWORD = "TU_PASSWORD"

def get_data():
    # 🔥 ejemplo con Binance
    r = requests.get("https://api.binance.com/api/v3/ticker/24hr?symbol=BTCUSDT")
    d = r.json()

    return {
        "price": float(d["lastPrice"]),
        "volume": float(d["volume"]),
        "vol_prom": float(d["volume"]) * 0.8,
        "delta": float(d["priceChangePercent"]),
        "trend": "up" if float(d["priceChangePercent"]) > 0 else "down"
    }

def run():
    iq = IQ_Option(EMAIL, PASSWORD)
    iq.connect()

    while True:
        data = get_data()

        señal = detectar_entrada(data)

        if señal:
            iq.buy(2, "EURUSD-OTC", señal, 1)
            print("🔥 ENTRADA REAL:", señal)

        time.sleep(5)

run()
