import time
import os
import requests
import sys
from iqoptionapi.stable_api import IQ_Option

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)

try:
    from estrategia import detectar_entrada_oculta
except Exception as e:
    print("❌ Error importando estrategia:", e)
    detectar_entrada_oculta = None


EMAIL = os.getenv("IQ_EMAIL")
PASSWORD = os.getenv("IQ_PASSWORD")

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

MONTO = 10000
CUENTA = "PRACTICE"

PARES = [
    "EURUSD-OTC",
    "GBPUSD-OTC",
    "USDHKD-OTC",
    "EURJPY-OTC",
    "EURGBP-OTC",
    "GBPJPY-OTC",
    "USDCHF-OTC"
]

bot_activo = True


# =========================
# TELEGRAM
# =========================
def enviar_mensaje(texto):
    try:
        requests.post(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            data={"chat_id": CHAT_ID, "text": texto},
            timeout=5
        )
    except:
        pass


# =========================
# ⏱ ESPERAR SIGUIENTE VELA
# =========================
def esperar_siguiente_vela():
    while True:
        ahora = time.time()
        restante = 60 - (ahora % 60)

        if restante <= 0.2:
            break

        time.sleep(0.05)


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
                enviar_mensaje("🤖 BOT CONECTADO")
                return iq
        except:
            pass

        time.sleep(5)


# =========================
# DATOS
# =========================
def obtener_velas(iq, par):
    try:
        velas = iq.get_candles(par, 60, 50, time.time())

        return [{
            "open": v["open"],
            "close": v["close"],
            "max": v["max"],
            "min": v["min"]
        } for v in velas]

    except:
        return None


# =========================
# OPERAR (ENTRADA EN SIGUIENTE VELA)
# =========================
def operar(iq, par, direccion, score):

    # ⏱ Esperar cierre de vela actual
    esperar_siguiente_vela()

    try:
        status, _ = iq.buy_digital_spot(par, MONTO, direccion, 1)

        if status:
            enviar_mensaje(f"""🚀 OPERACIÓN

Par: {par}
Dirección: {direccion.upper()}
Expiración: 1 MIN
""")

    except Exception as e:
        print("Error operar:", e)


# =========================
# MAIN
# =========================
def run():

    if detectar_entrada_oculta is None:
        return

    iq = conectar()

    while True:
        try:
            data = {}

            for par in PARES:
                velas = obtener_velas(iq, par)

                if velas:
                    data[par] = velas

                time.sleep(0.2)

            señal = detectar_entrada_oculta(data)

            if señal:
                par, direccion, score = señal

                enviar_mensaje(f"""🎯 SEÑAL

Par: {par}
Dirección: {direccion.upper()}
""")

                operar(iq, par, direccion, score)

                time.sleep(60)

            else:
                time.sleep(1)

        except Exception as e:
            print("Error:", e)
            iq = conectar()


if __name__ == "__main__":
    run()
