import time
import os
import requests
import sys
from iqoptionapi.stable_api import IQ_Option

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)

from estrategia import detectar_entrada_oculta

# =========================
# VALIDACIÓN ENV
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
    except Exception as e:
        print("Error Telegram:", e)


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
                time.sleep(1)

                try:
                    balance = iq.get_balance()
                except:
                    balance = "N/A"

                enviar_mensaje(f"🤖 BOT CONECTADO\nCuenta: DEMO\nBalance: {balance}")
                print("✅ Conectado correctamente")

                return iq

        except Exception as e:
            print("Error conexión:", e)

        time.sleep(5)


# =========================
# VERIFICAR CONEXIÓN
# =========================
def asegurar_conexion(iq):
    if not iq.check_connect():
        print("🔄 Reconectando...")
        return conectar()
    return iq


# =========================
# PARES ABIERTOS
# =========================
def obtener_pares_abiertos(iq):
    try:
        activos = iq.get_all_open_time()

        if "digital" not in activos:
            return []

        abiertos = [
            par for par, info in activos["digital"].items()
            if isinstance(info, dict) and info.get("open")
        ]

        return abiertos

    except Exception as e:
        print("Error activos:", e)
        return []


# =========================
# ESPERA VELA
# =========================
def esperar_nueva_vela():
    while True:
        t = time.time()
        if (t % 60) < 0.05:
            break
        time.sleep(0.01)

    time.sleep(1.2)


# =========================
# VELAS SEGURAS
# =========================
def obtener_velas(iq, par):
    try:
        velas = iq.get_candles(par, 60, 30, time.time())

        if not velas or len(velas) < 10:
            return None

        return [{
            "open": v.get("open"),
            "close": v.get("close"),
            "max": v.get("max"),
            "min": v.get("min")
        } for v in velas if all(k in v for k in ["open", "close", "max", "min"])]

    except Exception as e:
        print(f"Error velas {par}:", e)
        return None


# =========================
# OPERAR SEGURO
# =========================
def operar(iq, par, direccion):
    global ultima_entrada

    if time.time() - ultima_entrada < 30:
        return False

    enviar_mensaje(f"⏱ Preparando entrada en {par}")

    esperar_nueva_vela()

    try:
        iq.subscribe_strike_list(par, 1)
        time.sleep(0.5)

        status, order_id = iq.buy_digital_spot(par, MONTO, direccion, 1)

        iq.unsubscribe_strike_list(par, 1)

        if status:
            enviar_mensaje(f"""🚀 OPERACIÓN EJECUTADA

Par: {par}
Dirección: {direccion.upper()}
Expiración: 1 MIN
""")
            ultima_entrada = time.time()
            return True
        else:
            enviar_mensaje("❌ No ejecutó operación")
            return False

    except Exception as e:
        try:
            iq.unsubscribe_strike_list(par, 1)
        except:
            pass

        enviar_mensaje(f"❌ Error ejecución: {e}")
        return False


# =========================
# MAIN ROBUSTO
# =========================
def run():

    iq = conectar()

    while True:
        try:
            iq = asegurar_conexion(iq)

            data = {}
            pares = obtener_pares_abiertos(iq)

            if not pares:
                time.sleep(2)
                continue

            for par in pares:
                velas = obtener_velas(iq, par)

                if velas:
                    data[par] = velas

            if not data:
                time.sleep(1)
                continue

            señal = detectar_entrada_oculta(data)

            if señal and len(señal) == 3:
                par, direccion, _ = señal

                if par in data:
                    enviar_mensaje(f"🎯 SEÑAL DETECTADA\n{par} {direccion}")
                    operar(iq, par, direccion)

            time.sleep(0.3)

        except Exception as e:
            print("❌ Error crítico:", e)
            time.sleep(3)


if __name__ == "__main__":
    run()
