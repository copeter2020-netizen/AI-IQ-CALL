import time
import os
import requests
import sys
from iqoptionapi.stable_api import IQ_Option

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)

from estrategia import detectar_entrada

EMAIL = os.getenv("IQ_EMAIL")
PASSWORD = os.getenv("IQ_PASSWORD")

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

MONTO = 5
CUENTA = "PRACTICE"

PARES = ["EURUSD", "EURJPY"]


def enviar_mensaje(texto):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        requests.post(url, data={
            "chat_id": CHAT_ID,
            "text": texto
        }, timeout=5)
    except:
        pass


def conectar():
    while True:
        try:
            iq = IQ_Option(EMAIL, PASSWORD)
            iq.connect()

            if iq.check_connect():
                iq.change_balance(CUENTA)
                print("✅ CONECTADO A IQ OPTION")
                return iq

        except Exception as e:
            print("Error conexión:", e)

        time.sleep(5)


def obtener_velas(iq, par):
    try:
        velas = iq.get_candles(par, 60, 100, time.time())

        return [{
            "open": v["open"],
            "close": v["close"],
            "max": v["max"],
            "min": v["min"]
        } for v in velas]

    except Exception as e:
        print(f"Error velas {par}:", e)
        return []


def par_disponible(iq, par):
    try:
        activos = iq.get_all_open_time()

        return activos["binary"][par]["open"]

    except:
        return False


def operar(iq, par, direccion):

    if not par_disponible(iq, par):
        print(f"❌ {par} no disponible")
        return

    try:
        check, id = iq.buy(MONTO, par, direccion, 1)

        if check:
            print(f"🚀 OPERANDO {par} {direccion}")

            enviar_mensaje(f"""
🚀 ENTRADA EJECUTADA

Par: {par}
Dirección: {direccion.upper()}
Expiración: 5 MIN
Monto: ${MONTO}
""")
        else:
            print(f"❌ Fallo al ejecutar {par}")

    except Exception as e:
        print("Error al operar:", e)


def run():

    iq = conectar()

    while True:
        try:
            data = {}

            for par in PARES:
                velas = obtener_velas(iq, par)

                if velas:
                    data[par] = velas

            señal = detectar_entrada(data)

            if señal:
                par, direccion = señal

                print(f"🎯 SEÑAL: {par} {direccion}")

                operar(iq, par, direccion)

                time.sleep(300)

            else:
                time.sleep(1)

        except Exception as e:
            print("Error general:", e)
            time.sleep(5)


if __name__ == "__main__":
    run()
