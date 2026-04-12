import time
import os
import requests
import sys
from iqoptionapi.stable_api import IQ_Option

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)

from estrategia import detectar_entrada_oculta

# =========================
# VARIABLES
# =========================
EMAIL = os.getenv("IQ_EMAIL")
PASSWORD = os.getenv("IQ_PASSWORD")
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

if not all([EMAIL, PASSWORD, TOKEN, CHAT_ID]):
    raise Exception("❌ Faltan variables de entorno")

MONTO = 6
CUENTA = "PRACTICE"

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
# CONEXIÓN SEGURA
# =========================
def conectar():
    while True:
        try:
            iq = IQ_Option(EMAIL, PASSWORD)
            iq.connect()

            if iq.check_connect():

                iq.change_balance("PRACTICE")

                # 🔥 IMPORTANTE: estabilizar API
                iq.get_all_ACTIVES_OPCODE()
                time.sleep(2)

                enviar_mensaje("🤖 BOT CONECTADO (DEMO)")
                print("✅ Conectado")

                return iq

        except Exception as e:
            print("Error conexión:", e)

        time.sleep(5)


# =========================
# RECONEXIÓN
# =========================
def asegurar_conexion(iq):
    try:
        if not iq.check_connect():
            return conectar()
        return iq
    except:
        return conectar()


# =========================
# LISTA FIJA (EVITA BUG API)
# =========================
PARES = [
    "EURUSD-OTC",
    "GBPUSD-OTC",
    "USDHKD-OTC",
    "EURJPY-OTC",
    "GBPJPY-OTC",
    "USDCHF-OTC"
]


# =========================
# ESPERA VELA
# =========================
def esperar_nueva_vela():
    while True:
        if (time.time() % 60) < 0.05:
            break
        time.sleep(0.01)

    time.sleep(1.2)


# =========================
# OBTENER VELAS
# =========================
def obtener_velas(iq, par):
    try:
        velas = iq.get_candles(par, 60, 30, time.time())

        if not velas:
            return None

        return [{
            "open": v["open"],
            "close": v["close"],
            "max": v["max"],
            "min": v["min"]
        } for v in velas]

    except:
        return None


# =========================
# OPERAR (AISLADO DEL ERROR)
# =========================
def operar(iq, par, direccion):
    global ultima_entrada

    if time.time() - ultima_entrada < 30:
        return False

    enviar_mensaje(f"⏱ Preparando entrada {par}")

    esperar_nueva_vela()

    try:
        # 🔥 Esto evita fallo interno
        iq.subscribe_strike_list(par, 1)
        time.sleep(0.5)

        status, _ = iq.buy_digital_spot(par, MONTO, direccion, 1)

        iq.unsubscribe_strike_list(par, 1)

        if status:
            enviar_mensaje(f"🚀 {par} {direccion.upper()}")
            ultima_entrada = time.time()
            return True

        else:
            enviar_mensaje("❌ No ejecutó")
            return False

    except Exception as e:
        try:
            iq.unsubscribe_strike_list(par, 1)
        except:
            pass

        enviar_mensaje(f"❌ Error: {e}")
        return False


# =========================
# MAIN
# =========================
def run():

    iq = conectar()

    while True:
        try:
            iq = asegurar_conexion(iq)

            data = {}

            for par in PARES:
                velas = obtener_velas(iq, par)

                if velas:
                    data[par] = velas

            if not data:
                time.sleep(1)
                continue

            señal = detectar_entrada_oculta(data)

            if señal:
                par, direccion, _ = señal

                enviar_mensaje(f"🎯 SEÑAL {par} {direccion}")

                operar(iq, par, direccion)

            time.sleep(0.3)

        except Exception as e:
            print("Error general:", e)
            time.sleep(2)


if __name__ == "__main__":
    run()
