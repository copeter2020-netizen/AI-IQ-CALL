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

MONTO = 10000
CUENTA = "PRACTICE"

PARES = [
    "EURUSD-OTC",
    "GBPUSD-OTC",
    "USDJPY-OTC",
    "EURJPY-OTC",
    "GBPJPY-OTC"
]

ultima_entrada = 0


# =========================
# TELEGRAM
# =========================
def enviar_mensaje(msg):
    try:
        requests.post(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            data={"chat_id": CHAT_ID, "text": msg},
            timeout=5
        )
    except:
        pass


# =========================
# ESPERA EXACTA NUEVA VELA
# =========================
def esperar_nueva_vela():
    while True:
        t = time.time()
        if (t % 60) < 0.05:
            break
        time.sleep(0.01)

    time.sleep(1.2)


# =========================
# CONEXIÓN
# =========================
def conectar():
    while True:
        iq = IQ_Option(EMAIL, PASSWORD)
        iq.connect()

        if iq.check_connect():
            iq.change_balance(CUENTA)
            enviar_mensaje("🤖 BOT CONECTADO")
            return iq

        time.sleep(5)


# =========================
# DATOS
# =========================
def obtener_velas(iq, par):
    try:
        velas = iq.get_candles(par, 60, 20, time.time())
        return [{
            "open": v["open"],
            "close": v["close"],
            "max": v["max"],
            "min": v["min"]
        } for v in velas]
    except:
        return None


# =========================
# OPERAR
# =========================
def operar(iq, par, direccion):

    global ultima_entrada

    if time.time() - ultima_entrada < 30:
        return

    enviar_mensaje("⏱ Esperando continuidad...")

    esperar_nueva_vela()

    status, _ = iq.buy_digital_spot(par, MONTO, direccion, 1)

    if status:
        enviar_mensaje(f"🚀 {par} {direccion.upper()}")
        ultima_entrada = time.time()
    else:
        enviar_mensaje("❌ Falló entrada")


# =========================
# MAIN
# =========================
def run():

    iq = conectar()

    while True:
        try:
            data = {}

            for par in PARES:
                velas = obtener_velas(iq, par)
                if velas:
                    data[par] = velas

            señal = detectar_entrada_oculta(data)

            if señal:
                par, direccion, _ = señal

                enviar_mensaje(f"🎯 SEÑAL CONFIRMADA {par} {direccion}")

                operar(iq, par, direccion)

            time.sleep(0.2)

        except Exception as e:
            print(e)
            iq = conectar()


if __name__ == "__main__":
    run()
