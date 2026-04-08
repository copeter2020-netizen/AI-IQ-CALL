import time
import os
import requests
from iqoptionapi.stable_api import IQ_Option

from estrategia import detectar_entrada_oculta
from control import obtener_comandos, enviar

EMAIL = os.getenv("IQ_EMAIL")
PASSWORD = os.getenv("IQ_PASSWORD")

MONTO = 15000
CUENTA = "PRACTICE"

PARES = [
    "EURUSD-OTC",
    "EURJPY-OTC",
    "EURGBP-OTC",
    "GBPUSD-OTC",
    "USDJPY-OTC"
]


def conectar():
    while True:
        try:
            iq = IQ_Option(EMAIL, PASSWORD)
            iq.connect()

            if iq.check_connect():
                iq.change_balance(CUENTA)
                print("✅ CONECTADO")
                enviar("✅ BOT CONECTADO")
                return iq

        except Exception as e:
            print("Error conexión:", e)

        time.sleep(5)


def obtener_velas(iq, par):
    try:
        velas = iq.get_candles(par, 60, 40, time.time())

        return [{
            "open": v["open"],
            "close": v["close"],
            "max": v["max"],
            "min": v["min"]
        } for v in velas]

    except:
        return []


# ⏱ ENTRADA EXACTA AL CIERRE
def esperar_cierre():
    while True:
        if int(time.time()) % 60 == 59:
            return
        time.sleep(0.2)


def operar(iq, par, direccion):
    try:
        esperar_cierre()

        check, _ = iq.buy(MONTO, par, direccion, 3)

        if check:
            print(f"🚀 {par} {direccion}")

            enviar(f"""
🚀 ENTRADA

Par: {par}
Dirección: {direccion.upper()}
Expiración: 3 MIN
Monto: ${MONTO}
""")

    except Exception as e:
        print("Error operar:", e)


def run():

    iq = conectar()

    while True:
        try:

            # 🔥 CONTROL TELEGRAM
            activo = obtener_comandos()

            if not activo:
                time.sleep(1)
                continue

            data = {}

            for par in PARES:
                data[par] = obtener_velas(iq, par)

            señal = detectar_entrada_oculta(data)

            if señal:
                par, direccion, score = señal

                print(f"🎯 {par} {direccion} Score:{score}")

                enviar(f"🎯 Señal {par} {direccion} Score:{score}")

                operar(iq, par, direccion)

                time.sleep(180)

            else:
                time.sleep(0.3)

        except Exception as e:
            print("Error loop:", e)
            time.sleep(5)


if __name__ == "__main__":
    run()
