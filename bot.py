import time
import os
import requests
from iqoptionapi.stable_api import IQ_Option
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from estrategia import detectar_entrada_oculta

EMAIL = os.getenv("IQ_EMAIL")
PASSWORD = os.getenv("IQ_PASSWORD")

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

MONTO = 1.75
CUENTA = "PRACTICE"

PARES = [
    "EURUSD-OTC",
    "GBPUSD-OTC",
    "EURJPY-OTC",
    "EURGBP-OTC",
    "GBPJPY-OTC",
    "USDCHF-OTC"
]

# =========================
def enviar_mensaje(texto):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": texto})
    except:
        pass

# =========================
def conectar():
    while True:
        iq = IQ_Option(EMAIL, PASSWORD)
        iq.connect()

        if iq.check_connect():
            iq.change_balance(CUENTA)
            print("✅ CONECTADO")
            return iq

        time.sleep(5)

# =========================
def esperar_apertura():
    while True:
        if int(time.time()) % 60 == 0:
            return
        time.sleep(0.2)

# =========================
def obtener_velas(iq, par):
    velas = iq.get_candles(par, 60, 40, time.time())
    return [{
        "open": v["open"],
        "close": v["close"],
        "max": v["max"],
        "min": v["min"]
    } for v in velas]

# =========================
def operar(iq, par, direccion):

    esperar_apertura()

    check, _ = iq.buy(MONTO, par, direccion, 3)

    if check:
        print("🚀 ENTRADA", par, direccion)

        enviar_mensaje(f"""
🚀 ENTRADA PRO

Par: {par}
Dirección: {direccion}
Expiración: 3 MIN
Monto: {MONTO}
""")

# =========================
def run():

    iq = conectar()

    while True:
        try:

            data = {par: obtener_velas(iq, par) for par in PARES}

            señal = detectar_entrada_oculta(data)

            if señal:
                par, direccion, score = señal

                print("🎯 Señal:", par, direccion, score)

                operar(iq, par, direccion)

                time.sleep(180)

            else:
                time.sleep(0.5)

        except Exception as e:
            print("Error:", e)
            time.sleep(5)

# =========================
if __name__ == "__main__":
    run()
