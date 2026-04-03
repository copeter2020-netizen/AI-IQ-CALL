import time
import os
import requests
from iqoptionapi.stable_api import IQ_Option
from estrategia import detectar_mejor_entrada

EMAIL = os.getenv("IQ_EMAIL")
PASSWORD = os.getenv("IQ_PASSWORD")

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

MONTO = 10
CUENTA = "PRACTICE"

PARES = [
    "EURUSD-OTC",
    "GBPUSD-OTC",
    "EURJPY-OTC",
    "EURGBP-OTC",
    "USDCHF-OTC"
]


def enviar_mensaje(texto):
    try:
        if TOKEN and CHAT_ID:
            requests.post(
                f"https://api.telegram.org/bot{TOKEN}/sendMessage",
                data={"chat_id": CHAT_ID, "text": texto},
                timeout=5
            )
    except:
        pass


def conectar():
    while True:
        try:
            iq = IQ_Option(EMAIL, PASSWORD)
            iq.connect()

            if iq.check_connect():
                print("✅ CONECTADO")
                iq.change_balance(CUENTA)
                return iq
            else:
                time.sleep(5)
        except:
            time.sleep(5)


def obtener_velas(iq, par):
    try:
        velas = iq.get_candles(par, 60, 120, time.time())
        return velas if velas else []
    except:
        return []


def operar(iq, par, direccion):

    print(f"🔥 {par} → {direccion}")

    check, _ = iq.buy(MONTO, par, direccion, 1)

    if check:
        print("✅ OPERACIÓN ABIERTA")
        enviar_mensaje(f"{par} → {direccion.upper()} 🚀")
    else:
        print("❌ ERROR")


def run():

    iq = conectar()

    while True:
        try:

            if not iq.check_connect():
                iq = conectar()

            data = {par: obtener_velas(iq, par) for par in PARES}

            resultado = detectar_mejor_entrada(data)

            if resultado:
                par, direccion, score = resultado

                print(f"🎯 SNIPER ({score})")

                # ⏱️ ENTRADA EXACTA 59.9
                while True:
                    if time.time() % 60 >= 59.9:
                        break

                operar(iq, par, direccion)

                time.sleep(60)

            else:
                print("🔎 MODO SNIPER...")

            time.sleep(1)

        except Exception as e:
            print("ERROR:", e)
            time.sleep(5)


if __name__ == "__main__":
    run() 
