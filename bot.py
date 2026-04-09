import time
import os
import requests
from iqoptionapi.stable_api import IQ_Option
from estrategia import detectar_entrada_oculta


EMAIL = os.getenv("IQ_EMAIL")
PASSWORD = os.getenv("IQ_PASSWORD")

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

MONTO = 3.33
CUENTA = "PRACTICE"

# SOLO MERCADO REAL
PARES = [
    "EURUSD",
    "EURJPY"
]


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
                print("✅ CONECTADO")
                return iq

        except:
            time.sleep(5)


# ⏱ Entrada exacta
def esperar_cierre():
    while True:
        if int(time.time()) % 60 == 0:
            return
        time.sleep(0.01)


def obtener_velas(iq, par):
    try:
        velas = iq.get_candles(par, 60, 50, time.time())

        return [{
            "open": v["open"],
            "close": v["close"],
            "max": v["max"],
            "min": v["min"]
        } for v in velas]

    except:
        return []


def operar(iq, par, direccion):

    esperar_cierre()

    check, _ = iq.buy(MONTO, par, direccion, 5)

    if check:
        print(f"🚀 {par} {direccion}")

        enviar_mensaje(f"""
🚀 ENTRADA MOMENTUM

Par: {par}
Dirección: {direccion.upper()}
Expiración: 5 MIN
Monto: ${MONTO}

⚡ Estrategia: Momentum puro
""")


def run():

    iq = conectar()

    while True:
        try:
            data = {}

            for par in PARES:
                data[par] = obtener_velas(iq, par)

            señal = detectar_entrada_oculta(data)

            if señal:
                par, direccion, score = señal

                print(f"🎯 {par} {direccion} Score:{score:.2f}")

                operar(iq, par, direccion)

                time.sleep(300)

            else:
                time.sleep(0.3)

        except Exception as e:
            print("Error:", e)
            time.sleep(5)


if __name__ == "__main__":
    run()
