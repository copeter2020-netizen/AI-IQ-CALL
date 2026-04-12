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

MONTO = 3
CUENTA = "PRACTICE"

# 🔥 LISTA REAL (MENOS ERRORES)
PARES = [
    "EURUSD-OTC",
    "GBPUSD-OTC",
    "USDZAR-OTC",
    "EURJPY-OTC",
    "GBPJPY-OTC",
    "USDCHF-OTC"
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
# VALIDAR PAR DISPONIBLE
# =========================
def par_abierto(iq, par):
    try:
        activos = iq.get_all_open_time()
        return activos["digital"][par]["open"]
    except:
        return False


# =========================
# ESPERA NUEVA VELA
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
        velas = iq.get_candles(par, 60, 30, time.time())
        return [{
            "open": v["open"],
            "close": v["close"],
            "max": v["max"],
            "min": v["min"]
        } for v in velas]
    except:
        return None


# =========================
# OPERAR (CORREGIDO)
# =========================
def operar(iq, par, direccion):

    global ultima_entrada

    if time.time() - ultima_entrada < 30:
        return

    if not par_abierto(iq, par):
        enviar_mensaje(f"❌ {par} cerrado")
        return

    enviar_mensaje("⏱ Esperando vela...")

    esperar_nueva_vela()

    try:
        # 🔥 NECESARIO PARA OTC
        iq.subscribe_strike_list(par, 1)

        status, _ = iq.buy_digital_spot(par, MONTO, direccion, 1)

        iq.unsubscribe_strike_list(par, 1)

        if status:
            enviar_mensaje(f"🚀 {par} {direccion.upper()}")
            ultima_entrada = time.time()
        else:
            enviar_mensaje("❌ No ejecutó")

    except Exception as e:
        enviar_mensaje(f"❌ Error: {e}")


# =========================
# MAIN
# =========================
def run():

    iq = conectar()

    while True:
        try:
            data = {}

            for par in PARES:

                if not par_abierto(iq, par):
                    continue

                velas = obtener_velas(iq, par)

                if velas:
                    data[par] = velas

            señal = detectar_entrada_oculta(data)

            if señal:
                par, direccion, _ = señal

                enviar_mensaje(f"🎯 {par} {direccion}")

                operar(iq, par, direccion)

            time.sleep(0.3)

        except Exception as e:
            print(e)
            iq = conectar()


if __name__ == "__main__":
    run()
