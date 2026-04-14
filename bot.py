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

MONTO = 3
CUENTA = "PRACTICE"

ultima_entrada = 0
ultimo_par = None
operando = False
api_estable = True


# =========================
# TELEGRAM (NO BLOQUEANTE)
# =========================
def enviar_telegram(msg):
    def enviar():
        try:
            url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
            requests.post(
                url,
                data={
                    "chat_id": CHAT_ID,
                    "text": msg
                },
                timeout=5
            )
        except:
            pass

    threading.Thread(target=enviar, daemon=True).start()


# =========================
# LOG
# =========================
def log(msg):
    print(msg)
    enviar_telegram(msg)


# =========================
# CONEXIÓN
# =========================
def conectar():
    global api_estable

    while True:
        try:
            iq = IQ_Option(EMAIL, PASSWORD)
            iq.connect()

            if iq.check_connect():
                iq.change_balance(CUENTA)

                log("🔌 Conectando y calentando API...")

                for _ in range(5):
                    try:
                        iq.get_all_open_time()
                        time.sleep(1)
                    except:
                        pass

                api_estable = True
                log("✅ BOT CONECTADO")
                return iq

        except Exception as e:
            log(f"❌ Error conexión: {e}")

        time.sleep(5)


def asegurar_conexion(iq):
    global api_estable

    try:
        if not iq.check_connect():
            api_estable = False
            log("🔄 Reconectando...")
            return conectar()
        return iq
    except:
        api_estable = False
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
        return iq.get_all_open_time()["digital"][par]["open"]
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
# OPERAR
# =========================
def operar(iq, par, direccion):
    global ultima_entrada, operando, api_estable

    if operando:
        return False

    if time.time() - ultima_entrada < 30:
        return False

    if not activo_abierto(iq, par):
        return False

    operando = True

    esperar_entrada()

    try:
        iq.subscribe_strike_list(par, 1)
        time.sleep(1)

        status, order_id = iq.buy_digital_spot(par, MONTO, direccion, 1)

        iq.unsubscribe_strike_list(par, 1)

        if status:
            mensaje = f"""✅ OPERACIÓN EJECUTADA

Par: {par}
Dirección: {direccion.upper()}
Monto: ${MONTO}
ID: {order_id}
"""
            log(mensaje)
            ultima_entrada = time.time()
        else:
            log("❌ No ejecutó la operación")

    except KeyError:
        log("⚠️ ERROR UNDERLYING → REINICIANDO API")
        api_estable = False
        iq = conectar()

    except Exception as e:
        log(f"❌ Error operación: {e}")

    operando = False
    return True


# =========================
# MAIN
# =========================
def run():
    global ultimo_par, api_estable

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

                if par == ultimo_par:
                    continue

                mensaje = f"""📊 SEÑAL DETECTADA

Par: {par}
Dirección: {direccion.upper()}
Score: {score}
"""
                log(mensaje)

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
