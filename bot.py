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

if not all([EMAIL, PASSWORD, TOKEN, CHAT_ID]):
    raise Exception("Faltan variables de entorno")

MONTO = 3
CUENTA = "PRACTICE"

ultima_entrada = 0
api_estable = False


# =========================
# LOG
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
# CONEXIÓN + WARMUP
# =========================
def conectar():
    global api_estable

    while True:
        try:
            iq = IQ_Option(EMAIL, PASSWORD)
            iq.connect()

            if iq.check_connect():
                iq.change_balance(CUENTA)

                log("Calentando API...")

                # 🔥 WARMUP REAL (CLAVE)
                for i in range(6):
                    try:
                        iq.get_all_open_time()
                        iq.get_candles("EURUSD-OTC", 60, 5, time.time())
                        time.sleep(1)
                    except:
                        pass

                api_estable = True
                log("BOT CONECTADO Y ESTABLE")
                return iq

        except Exception as e:
            log(f"Error conexión: {e}")

        time.sleep(5)


# =========================
# RECONEXIÓN
# =========================
def asegurar_conexion(iq):
    global api_estable

    try:
        if not iq.check_connect():
            api_estable = False
            log("Reconectando...")
            return conectar()
        return iq
    except:
        api_estable = False
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
# VALIDAR ACTIVO
# =========================
def activo_abierto(iq, par):
    try:
        info = iq.get_all_open_time()
        return info["digital"][par]["open"]
    except:
        return False


# =========================
# ESPERA
# =========================
def esperar_entrada():
    while True:
        if int(time.time() % 60) >= 58:
            break
        time.sleep(0.005)


# =========================
# VELAS
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
# OPERAR (ANTI CRASH TOTAL)
# =========================
def operar(iq, par, direccion):
    global ultima_entrada, api_estable

    if not api_estable:
        log("API inestable - evitando operación")
        return False

    if time.time() - ultima_entrada < 20:
        return False

    if not activo_abierto(iq, par):
        return False

    esperar_entrada()

    # 🔥 RETRY CONTROLADO
    for intento in range(3):
        try:
            iq.subscribe_strike_list(par, 1)
            time.sleep(0.8)

            status, order_id = iq.buy_digital_spot(par, MONTO, direccion, 1)

            iq.unsubscribe_strike_list(par, 1)

            if status and order_id:
                log(f"""✅ TRADE

{par} {direccion}
ID: {order_id}
""")
                ultima_entrada = time.time()
                return True

        except KeyError:
            log(f"Error underlying intento {intento+1}")
            api_estable = False
            time.sleep(2)
            return False

        except Exception as e:
            log(f"Error trade: {e}")
            time.sleep(1)

    return False


# =========================
# MAIN
# =========================
def run():

    iq = conectar()

    while True:
        try:
            iq = asegurar_conexion(iq)

            if not api_estable:
                time.sleep(2)
                continue

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

                log(f"SEÑAL {par} {direccion} score {score}")

                # 🔥 CONFIRMACIÓN FINAL
                velas_final = obtener_velas(iq, par)

                if not velas_final:
                    continue

                confirmacion = detectar_entrada_oculta({par: velas_final})

                if confirmacion:
                    operar(iq, par, direccion)

            time.sleep(0.2)

        except Exception as e:
            log(f"Error general: {e}")
            time.sleep(2)


if __name__ == "__main__":
    run()
