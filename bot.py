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

                # 🔥 FORZAR CARGA DE ACTIVOS
                for _ in range(3):
                    try:
                        iq.get_all_open_time()
                        time.sleep(1)
                    except:
                        pass

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
# VALIDAR ACTIVO
# =========================
def activo_abierto(iq, par):
    try:
        info = iq.get_all_open_time()
        return info["digital"][par]["open"]
    except:
        return False


# =========================
# ESPERA SEGUNDO 58
# =========================
def esperar_entrada():
    while True:
        segundos = int(time.time() % 60)
        if segundos >= 58:
            break
        time.sleep(0.01)


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
# OPERAR (ANTI ERROR UNDERLYING)
# =========================
def operar(iq, par, direccion):
    global ultima_entrada

    if time.time() - ultima_entrada < 20:
        return False

    if not activo_abierto(iq, par):
        log(f"{par} cerrado")
        return False

    log(f"Preparando entrada {par}")

    esperar_entrada()

    try:
        # 🔥 PROTECCIÓN CLAVE
        try:
            iq.subscribe_strike_list(par, 1)
            time.sleep(0.7)
        except KeyError:
            log("⚠️ Error underlying (subscribe) - reintentando...")
            time.sleep(2)
            return False

        status, order_id = iq.buy_digital_spot(par, MONTO, direccion, 1)

        try:
            iq.unsubscribe_strike_list(par, 1)
        except:
            pass

        if status and order_id:
            log(f"""✅ OPERACIÓN EJECUTADA

{par} {direccion.upper()}
ID: {order_id}
""")
            ultima_entrada = time.time()
            return True
        else:
            log("❌ No ejecutó la orden")
            return False

    except KeyError:
        log("⚠️ Error underlying (buy) - ignorado")
        return False

    except Exception as e:
        log(f"Error operación: {e}")
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

                # 🔥 CONFIRMACIÓN FINAL
                velas_final = obtener_velas(iq, par)

                if not velas_final:
                    continue

                confirmacion = detectar_entrada_oculta({par: velas_final})

                if confirmacion:
                    operar(iq, par, direccion)
                else:
                    log("⚠️ Señal cancelada")

            time.sleep(0.2)

        except Exception as e:
            log(f"Error general: {e}")
            time.sleep(2)


if __name__ == "__main__":
    run()
