import os
import time
import sys
import requests
from iqoptionapi.stable_api import IQ_Option
from strategy import analyze_market


# ==========================
# TELEGRAM
# ==========================
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_message(text):
    try:
        if TOKEN and CHAT_ID:
            requests.post(
                f"https://api.telegram.org/bot{TOKEN}/sendMessage",
                data={"chat_id": CHAT_ID, "text": text},
                timeout=5
            )
    except:
        pass


def get_updates(offset=None):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
        params = {"timeout": 5}
        if offset:
            params["offset"] = offset

        r = requests.get(url, params=params, timeout=5).json()
        return r.get("result", [])
    except:
        return []


# ==========================
# CONTROL BOT
# ==========================
BOT_ACTIVO = True
LAST_UPDATE_ID = None


def check_telegram_commands():
    global BOT_ACTIVO, LAST_UPDATE_ID

    updates = get_updates(LAST_UPDATE_ID)

    for update in updates:

        LAST_UPDATE_ID = update["update_id"] + 1

        if "message" not in update:
            continue

        text = update["message"].get("text", "")

        if text == "/stopbot":
            BOT_ACTIVO = False
            send_message("⛔ BOT DETENIDO")

        elif text == "/startbot":
            BOT_ACTIVO = True
            send_message("▶️ BOT ACTIVADO")


# ==========================
# SILENCIAR
# ==========================
class DevNull:
    def write(self, msg): pass
    def flush(self): pass


def silent(func, *args, **kwargs):
    old_stdout = sys.stdout
    old_stderr = sys.stderr
    sys.stdout = DevNull()
    sys.stderr = DevNull()
    try:
        return func(*args, **kwargs)
    except:
        return None
    finally:
        sys.stdout = old_stdout
        sys.stderr = old_stderr


# ==========================
# CONFIG
# ==========================
IQ_EMAIL = os.getenv("IQ_EMAIL")
IQ_PASSWORD = os.getenv("IQ_PASSWORD")

TIMEFRAME = 60
MONTO = 120
EXPIRACION = 1


# ==========================
# CONEXIÓN
# ==========================
def connect():
    while True:
        iq = IQ_Option(IQ_EMAIL, IQ_PASSWORD)
        silent(iq.connect)

        if iq.check_connect():
            send_message("✅ BOT CONECTADO")
            return iq

        time.sleep(5)


# ==========================
# OTC ABIERTOS
# ==========================
def get_otc_abiertos(iq):
    try:
        activos = iq.get_all_open_time()
        return [
            par for par, data in activos["binary"].items()
            if "-OTC" in par and data["open"]
        ]
    except:
        return []


# ==========================
# TIEMPO
# ==========================
def esperar_cierre():
    while int(time.time()) % 60 != 59:
        time.sleep(0.02)


def esperar_apertura():
    while int(time.time()) % 60 != 0:
        time.sleep(0.001)


# ==========================
# RESULTADO
# ==========================
def obtener_resultado(iq, trade_id):

    while True:
        result = silent(iq.check_win_v4, trade_id)

        if result is None:
            time.sleep(1)
            continue

        try:
            if isinstance(result, tuple):
                result = result[0]

            result = float(result)
        except:
            return "loss"

        if result > 0:
            return "win"
        elif result == 0:
            return "draw"
        else:
            return "loss"


# ==========================
# EJECUTAR
# ==========================
def ejecutar_trade(iq, pair, action):

    status, trade_id = silent(
        iq.buy, MONTO, pair, action, EXPIRACION
    )

    if not status:
        send_message(f"❌ Entrada rechazada {pair}")
        return

    send_message(f"📊 {action.upper()} {pair}")

    resultado = obtener_resultado(iq, trade_id)

    if resultado == "win":
        send_message(f"✅ WIN {pair}")
    elif resultado == "draw":
        send_message(f"➖ DRAW {pair}")
    else:
        send_message(f"❌ LOSS {pair}")


# ==========================
# BOT
# ==========================
def run():

    iq = connect()

    while True:

        check_telegram_commands()

        if not BOT_ACTIVO:
            time.sleep(1)
            continue

        esperar_cierre()

        pares = get_otc_abiertos(iq)

        for par in pares:

            candles = silent(
                iq.get_candles, par, TIMEFRAME, 70, time.time()
            )

            if not candles:
                continue

            señal = analyze_market(candles, None, None)

            if not señal:
                continue

            action = señal["action"]  # 🔥 ahora usa CALL o PUT

            send_message(f"📡 SEÑAL {action.upper()} {par}")

            esperar_apertura()

            ejecutar_trade(iq, par, action)

            break


if __name__ == "__main__":
    run()
