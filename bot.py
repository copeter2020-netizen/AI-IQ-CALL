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

if not all([EMAIL, PASSWORD, TOKEN, CHAT_ID]):
    raise Exception("Faltan variables de entorno")

MONTO = 9
CUENTA = "PRACTICE"

ultima_entrada = 0
ultimo_par = None
operando = False


# =========================
# TELEGRAM
# =========================
def enviar_telegram(msg):
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
            log(f"❌ Error conexión: {e}")

        time.sleep(5)


def asegurar_conexion(iq):
    try:
        if not iq.check_connect():
            log("🔄 Reconectando...")
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


def esperar_entrada():
    while int(time.time() % 60) < 58:
        time.sleep(0.005)


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
# OPERAR (SIN DIGITAL)
# =========================
def operar(iq, par, direccion):
    global ultima_entrada, operando

    if operando:
        return False

    if time.time() - ultima_entrada < 30:
        return False

    if not activo_abierto(iq, par):
        return False

    operando = True

    esperar_entrada()

    try:
        status, order_id = iq.buy(MONTO, par, direccion, 1)

        if status:
            log(f"""✅ OPERACIÓN EJECUTADA

Par: {par}
Dirección: {direccion.upper()}
Monto: ${MONTO}
ID: {order_id}
""")
            ultima_entrada = time.time()
        else:
            log("❌ No ejecutó la operación")

    except Exception as e:
        log(f"❌ Error operación: {e}")

    operando = False
    return True


# =========================
# MAIN
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
                continue

            señal = detectar_entrada_oculta(data)

            if señal:
                par, direccion, score = señal

                if par == ultimo_par:
                    continue

                log(f"""📊 SEÑAL DETECTADA

Par: {par}
Dirección: {direccion.upper()}
Score: {score}
""")

                velas_final = obtener_velas(iq, par)

                if not velas_final:
                    continue

                confirmacion = detectar_entrada_oculta({par: velas_final})

                if confirmacion:
                    operar(iq, par, direccion)
                    ultimo_par = par
                else:
                    log("⚠️ Señal cancelada")

            time.sleep(0.3)

        except Exception as e:
            log(f"❌ Error general: {e}")
            time.sleep(2)


if __name__ == "__main__":
    run()
