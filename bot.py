import time
import os
from iqoptionapi.stable_api import IQ_Option
from estrategia import detectar_mejor_entrada
from telegram_bot import enviar, escuchar

EMAIL = os.getenv("IQ_EMAIL")
PASSWORD = os.getenv("IQ_PASSWORD")

MONTO = 1000
CUENTA = "PRACTICE"

PARES = [
    "EURUSD-OTC","GBPUSD-OTC","USDCHF-OTC",
    "EURJPY-OTC","EURGBP-OTC","GBPJPY-OTC","AUDUSD-OTC","BTCUSD-OTC","ETHUSD-OTC"
]


def conectar():
    while True:
        try:
            iq = IQ_Option(EMAIL, PASSWORD)
            iq.connect()

            if iq.check_connect():
                iq.change_balance(CUENTA)
                print("BOT CONECTADO")
                return iq
        except:
            pass

        time.sleep(5)


def obtener_velas(iq, par):
    try:
        data = iq.get_candles(par, 60, 60, time.time())

        return [{
            "open": v["open"],
            "close": v["close"],
            "max": v["max"],
            "min": v["min"]
        } for v in data]

    except:
        return []


def operar(iq, par, direccion):
    check, _ = iq.buy(MONTO, par, direccion, 4)

    if check:
        print(f"SEÑAL → {par} {direccion}")
        enviar(f"🚀 {par} → {direccion.upper()}")


def run():
    iq = conectar()

    while True:
        try:

            activo = escuchar()

            if not activo:
                time.sleep(2)
                continue

            data = {}

            for par in PARES:
                data[par] = obtener_velas(iq, par)

            resultado = detectar_mejor_entrada(data)

            if resultado:
                par, direccion, _ = resultado

                segundos = int(time.time()) % 60
                esperar = 60 - segundos

                if esperar > 0:
                    time.sleep(esperar)

                operar(iq, par, direccion)

                time.sleep(240)

            else:
                time.sleep(2)

        except:
            time.sleep(5)


if __name__ == "__main__":
    run()
