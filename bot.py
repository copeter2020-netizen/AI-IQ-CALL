import time
import os
import requests
from iqoptionapi.stable_api import IQ_Option
from estrategia import detectar_mejor_entrada

EMAIL = os.getenv("IQ_EMAIL")
PASSWORD = os.getenv("IQ_PASSWORD")

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

MONTO = 2000
CUENTA = "PRACTICE"

PARES = [
    "EURUSD-OTC",
    "GBPUSD-OTC",
    "EURJPY-OTC",
    "USDCHF-OTC"
]

def enviar_mensaje(msg):
    try:
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={
            "chat_id": CHAT_ID,
            "text": msg
        })
    except:
        pass


def conectar():
    while True:
        iq = IQ_Option(EMAIL, PASSWORD)
        iq.connect()

        if iq.check_connect():
            iq.change_balance(CUENTA)
            print("✅ CONECTADO")
            return iq

        time.sleep(5)


def obtener_velas(iq, par):
    velas = iq.get_candles(par, 60, 60, time.time())

    return [{
        "open": v["open"],
        "close": v["close"],
        "max": v["max"],
        "min": v["min"]
    } for v in velas]


def operar(iq, par, direccion):

    check, _ = iq.buy(MONTO, par, direccion, 4)

    if check:
        print(f"🚀 {par} {direccion}")

        enviar_mensaje(f"""
🚀 ENTRADA EXTREMA

Par: {par}
Dirección: {direccion.upper()}
Expiración: 4 MIN
Monto: ${MONTO}
""")


def run():

    iq = conectar()

    while True:
        try:

            data = {}

            for par in PARES:
                data[par] = obtener_velas(iq, par)

            resultado = detectar_mejor_entrada(data)

            if resultado:
                par, direccion, score = resultado

                print(f"🔥 EXTREMO ({score})")

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
