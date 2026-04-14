import time
import os
import requests
import sys
from datetime import datetime
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

MONTO = 3
CUENTA = "PRACTICE"

ultima_entrada = 0


# =========================
# LOG + TELEGRAM
# =========================
def log(msg):
    print(msg)

    try:
        requests.post(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            data={"chat_id": CHAT_ID, "text": msg},
            timeout=5
        )
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
                iq.change_balance("PRACTICE")

                iq.update_ACTIVES_OPCODE()
                time.sleep(2)

                log("BOT CONECTADO DEMO")
                return iq

        except Exception as e:
            log(f"Error conexión: {e}")

        time.sleep(5)


# =========================
# RECONEXIÓN
# =========================
def asegurar_conexion(iq):
    try:
        if not iq.check_connect():
            log("Reconectando...")
            return conectar()

        iq.update_ACTIVES_OPCODE()
        return iq

    except:
        return conectar()


# =========================
# PARES ESTABLES
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
# ESPERA NUEVA VELA
# =========================
def esperar_nueva_vela():
    while True:
        now = datetime.now()
        if now.second == 0:
            break
        time.sleep(0.2)


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
# VALIDAR ACTIVO
# =========================
def activo_disponible(iq, par):
    try:
        activos = iq.get_all_ACTIVES_OPCODE()
        return par in activos
    except:
        return False


# =========================
# 🔥 OPERAR SNIPER REAL
# =========================
def operar(iq, par, direccion):
    global ultima_entrada

    if time.time() - ultima_entrada < 30:
        return False

    if not activo_disponible(iq, par):
        log(f"❌ Activo no disponible: {par}")
        return False

    log(f"🎯 SNIPER esperando {par}")

    # 🔥 ESPERA ULTRA PRECISA (59.5+)
    while True:
        ahora = time.time()
        segundos = int(ahora) % 60
        milisegundos = ahora - int(ahora)

        if segundos == 59 and milisegundos >= 0.5:
            break

        time.sleep(0.001)

    try:
        iq.subscribe_strike_list(par, 1)
        time.sleep(0.1)

        EXPIRACION = 1

        status, order_id = iq.buy_digital_spot(
            par,
            MONTO,
            direccion,
            EXPIRACION
        )

        try:
            iq.unsubscribe_strike_list(par, 1)
        except:
            pass

        if status:
            log(f"""🚀 SNIPER EJECUTADO

{par} {direccion.upper()}
Expiración: {EXPIRACION}M
Entrada: 59.5+
""")
            ultima_entrada = time.time()
            return True
        else:
            log("❌ SNIPER no ejecutó")
            return False

    except Exception as e:
        try:
            iq.unsubscribe_strike_list(par, 1)
        except:
            pass

        log(f"❌ Error sniper: {e}")
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
                par, direccion, score = señal

                log(f"""📊 SEÑAL DETECTADA

{par} {direccion}
Score: {score}
""")

                operar(iq, par, direccion)

            time.sleep(0.2)

        except Exception as e:
            log(f"❌ Error general: {e}")
            time.sleep(2)


if __name__ == "__main__":
    run()
