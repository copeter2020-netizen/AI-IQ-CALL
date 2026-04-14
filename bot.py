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
                iq.change_balance(CUENTA)
                iq.update_ACTIVES_OPCODE()
                log("✅ BOT CONECTADO")
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
        return iq
    except:
        return conectar()


# =========================
# PARES
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
# VERIFICAR SI ES BUEN MOMENTO DE ENTRAR
# =========================
def es_momento_entrada():
    now = datetime.now()
    return now.second >= 0 and now.second <= 3  # primeros segundos vela


# =========================
# OPERAR (SIN BLOQUEO)
# =========================
def operar(iq, par, direccion):
    global ultima_entrada

    if time.time() - ultima_entrada < 30:
        return False

    if not activo_disponible(iq, par):
        log(f"❌ Activo no disponible: {par}")
        return False

    # 🔥 SOLO ENTRA SI ESTÁ EN VENTANA CORRECTA
    if not es_momento_entrada():
        log("⏱ Esperando nueva vela sin bloquear...")
        return False

    try:
        iq.subscribe_strike_list(par, 1)
        time.sleep(0.2)

        status, order_id = iq.buy_digital_spot(par, MONTO, direccion, 1)

        try:
            iq.unsubscribe_strike_list(par, 1)
        except:
            pass

        if status:
            log(f"""✅ OPERACIÓN EJECUTADA

{par} {direccion.upper()}
Expiración: 1M
""")
            ultima_entrada = time.time()
            return True
        else:
            log("❌ No ejecutó la orden")
            return False

    except Exception as e:
        log(f"❌ Error operación: {e}")
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

            # 🔥 LOOP RÁPIDO Y NO BLOQUEANTE
            time.sleep(0.3)

        except Exception as e:
            log(f"❌ Error general: {e}")
            time.sleep(2)


if __name__ == "__main__":
    run()
