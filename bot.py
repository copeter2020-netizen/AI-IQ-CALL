import time
import os
import requests
import sys
import threading
from iqoptionapi.stable_api import IQ_Option

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)

from estrategia import detectar_entrada_oculta

EMAIL = os.getenv("IQ_EMAIL")
PASSWORD = os.getenv("IQ_PASSWORD")
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

if not all([EMAIL, PASSWORD]):
    raise Exception("Faltan credenciales IQ Option")

MONTO = 300
CUENTA = "PRACTICE"

ultima_entrada = 0
ultimo_par = None
operando = False


# =========================
# TELEGRAM
# =========================
def enviar_telegram(msg):
    if not TOKEN or not CHAT_ID:
        return

    def enviar():
        try:
            requests.post(
                f"https://api.telegram.org/bot{TOKEN}/sendMessage",
                data={"chat_id": CHAT_ID, "text": msg},
                timeout=5
            )
        except:
            pass

    threading.Thread(target=enviar, daemon=True).start()


def log(msg):
    print(msg)
    enviar_telegram(msg)


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
                log("✅ BOT CONECTADO")
                return iq

        except Exception as e:
            print(f"Error conexión: {e}")

        time.sleep(5)


def asegurar_conexion(iq):
    try:
        if not iq.check_connect():
            print("Reconectando...")
            return conectar()
        return iq
    except:
        return conectar()


# =========================
# CONFIG
# =========================
PARES = [
    "EURUSD-OTC",
    "GBPUSD-OTC",
    "USDZAR-OTC",
    "EURJPY-OTC",
    "GBPJPY-OTC",
    "USDCHF-OTC"
]


# =========================
# FUNCIONES
# =========================
def activo_abierto(iq, par):
    try:
        return iq.get_all_open_time()["binary"][par]["open"]
    except:
        return False


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
# OPERAR
# =========================
def operar(iq, par, direccion):
    global ultima_entrada, operando

    if operando:
        return False

    if time.time() - ultima_entrada < 10:
        return False

    if not activo_abierto(iq, par):
        return False

    operando = True

    try:
        status, order_id = iq.buy(MONTO, par, direccion, 1)

        if status:
            log(f"""🚀 OPERACIÓN

{par} {direccion.upper()}
ID: {order_id}
""")
            ultima_entrada = time.time()
        else:
            print("No ejecutó")

    except Exception as e:
        print(f"Error operación: {e}")

    operando = False
    return True


# =========================
# LOOP PRINCIPAL
# =========================
def run():
    global ultimo_par

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
                par, direccion, score = señal

                if par == ultimo_par:
                    continue

                log(f"""📊 SEÑAL

{par} {direccion}
Score: {score}
""")

                operar(iq, par, direccion)
                ultimo_par = par

            time.sleep(0.2)

        except Exception as e:
            print(f"Error loop: {e}")
            time.sleep(2)


# =========================
# 🔥 ANTI-CRASH LOOP (CLAVE)
# =========================
if __name__ == "__main__":
    while True:
        try:
            run()
        except Exception as e:
            print(f"🔥 BOT CRASH: {e}")
            time.sleep(5)
