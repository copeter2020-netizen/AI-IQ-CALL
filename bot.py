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

MONTO = 6

# 🔥 FORZAMOS DEMO
CUENTA = "PRACTICE"

ultima_entrada = 0


# =========================
# TELEGRAM
# =========================
def enviar_mensaje(msg):
    try:
        requests.post(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            data={
                "chat_id": CHAT_ID,
                "text": msg
            },
            timeout=5
        )
    except:
        pass


# =========================
# CONEXIÓN (100% DEMO)
# =========================
def conectar():
    while True:
        try:
            iq = IQ_Option(EMAIL, PASSWORD)
            iq.connect()

            if iq.check_connect():

                # 🔥 FORZAR CUENTA DEMO
                iq.change_balance("PRACTICE")

                time.sleep(1)

                balance = iq.get_balance()

                enviar_mensaje(f"""🤖 BOT CONECTADO

Cuenta: DEMO
Balance: ${balance}
""")

                print("✅ CONECTADO A DEMO")

                return iq

        except Exception as e:
            print("Error conexión:", e)

        time.sleep(5)


# =========================
# OBTENER PARES ABIERTOS
# =========================
def obtener_pares_abiertos(iq):
    try:
        activos = iq.get_all_open_time()
        abiertos = []

        for par, info in activos["digital"].items():
            if info["open"]:
                abiertos.append(par)

        return abiertos

    except:
        return []


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
# OBTENER VELAS
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
# OPERAR
# =========================
def operar(iq, par, direccion):
    global ultima_entrada

    if time.time() - ultima_entrada < 30:
        return False

    enviar_mensaje(f"⏱ Preparando entrada en {par}")

    esperar_nueva_vela()

    try:
        # 🔥 NECESARIO PARA OTC
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
            enviar_mensaje("❌ Falló ejecución")
            return False

    except Exception as e:
        enviar_mensaje(f"❌ Error ejecución: {e}")
        return False


# =========================
# MAIN
# =========================
def run():

    iq = conectar()

    while True:
        try:
            data = {}

            # 🔥 SOLO PARES ABIERTOS REALES
            pares = obtener_pares_abiertos(iq)

            if not pares:
                time.sleep(2)
                continue

            for par in pares:
                velas = obtener_velas(iq, par)

                if velas:
                    data[par] = velas

            señal = detectar_entrada_oculta(data)

            if señal:
                par, direccion, _ = señal

                enviar_mensaje(f"🎯 SEÑAL DETECTADA\n{par} {direccion}")

                operar(iq, par, direccion)

            time.sleep(0.3)

        except Exception as e:
            print("Error general:", e)
            iq = conectar()


if __name__ == "__main__":
    run()
