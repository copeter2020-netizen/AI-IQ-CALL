import time
import os
import requests
import sys
from iqoptionapi.stable_api import IQ_Option

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)

from estrategia import detectar_entrada_oculta

EMAIL = os.getenv("IQ_EMAIL")
PASSWORD = os.getenv("IQ_PASSWORD")

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

MONTO = 5
CUENTA = "PRACTICE"

PARES = [
    "EURUSD-OTC",
    "EURJPY-OTC",
    "EURGBP-OTC",
    "EURCHF-OTC",
    "EURAUD-OTC",
    "EURCAD-OTC",
    "GBPUSD-OTC",
    "GBPJPY-OTC",
    "GBPAUD-OTC",
    "GBPCAD-OTC",
    "GBPCHF-OTC",
    "USDJPY-OTC",
    "USDCHF-OTC",
    "USDCAD-OTC",
    "AUDUSD-OTC",
    "AUDJPY-OTC",
    "AUDCAD-OTC",
    "AUDCHF-OTC",
    "NZDJPY-OTC",
    "NZDCAD-OTC",
    "CADJPY-OTC",
    "CHFJPY-OTC", 
    "USDNOK-OTC",
    "USDSEK-OTC",
    "USDTRY-OTC",
    "USDZAR-OTC",
    "BTCUSD-OTC",
    "ETHUSD-OTC",
    "LTCUSD-OTC"
]


# =========================
# TELEGRAM
# =========================
def enviar_mensaje(texto):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        requests.post(url, data={
            "chat_id": CHAT_ID,
            "text": texto
        }, timeout=5)
    except:
        pass


# =========================
# CONEXIÓN
# =========================
def conectar():
    while True:
        try:
            iq = IQ_Option(EMAIL, PASSWORD)
            iq.connect()

            if iq.check_connect():
                iq.change_balance(CUENTA)
                print("✅ CONECTADO")
                enviar_mensaje("✅ BOT CONECTADO")
                return iq

        except:
            pass

        time.sleep(5)


# =========================
# ⏱ ENTRADA EXACTA
# =========================
def esperar_cierre():
    while True:
        ahora = time.time()

        if int(ahora) % 60 == 59 and (ahora - int(ahora)) > 0.8:
            return

        time.sleep(0.01)


# =========================
# DATOS
# =========================
def obtener_velas(iq, par):
    try:
        velas = iq.get_candles(par, 60, 50, time.time() - 2)

        return [{
            "open": v["open"],
            "close": v["close"],
            "max": v["max"],
            "min": v["min"]
        } for v in velas]

    except:
        return []


# =========================
# OPERAR
# =========================
def operar(iq, par, direccion):

    esperar_cierre()

    check, _ = iq.buy(MONTO, par, direccion, 1)

    if check:
        print(f"🚀 {par} {direccion}")

        enviar_mensaje(f"""
🚀 ENTRADA CONSOLIDACIÓN

Par: {par}
Dirección: {direccion.upper()}
Expiración: 3 MIN
Monto: ${MONTO}

📊 Estrategia: Rango + Reversión
""")


# =========================
# MAIN
# =========================
def run():

    iq = conectar()

    ultima_operacion = 0

    while True:
        try:
            if time.time() - ultima_operacion < 60:
                time.sleep(0.2)
                continue

            data = {}

            for par in PARES:
                data[par] = obtener_velas(iq, par)

            señal = detectar_entrada_oculta(data)

            if señal:
                par, direccion, score = señal

                print(f"🎯 {par} {direccion} Score:{score}")

                operar(iq, par, direccion)

                ultima_operacion = time.time()

                time.sleep(180)

            else:
                time.sleep(0.3)

        except Exception as e:
            print("Error:", e)
            time.sleep(5)


if __name__ == "__main__":
    run()
