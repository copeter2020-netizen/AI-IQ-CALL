import os
import time
import sys
import requests

# 🔥 BLOQUEAR LOGS DE LA LIBRERÍA
sys.stderr = open(os.devnull, 'w')

from iqoptionapi.stable_api import IQ_Option
from strategy import analyze_market


# ==========================
# 🔥 FIX GLOBAL (ANTES DE TODO)
# ==========================
def disable_digital(iq):
    try:
        iq.api.digital_underlying_list = {"underlying": {}}
        iq.api.get_digital_underlying_list_data = lambda x: {"underlying": {}}
        iq.api.subscribe_digital_underlying = lambda *args, **kwargs: None
        iq.api.unsubscribe_digital_underlying = lambda *args, **kwargs: None
        iq.api.get_digital_current_profit = lambda *args, **kwargs: None
    except:
        pass


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


# ==========================
# SILENCIAR TODO
# ==========================
class DevNull:
    def write(self, msg): pass
    def flush(self): pass


def silent(func, *args, **kwargs):
    old_stdout = sys.stdout
    sys.stdout = DevNull()
    try:
        return func(*args, **kwargs)
    except:
        return None
    finally:
        sys.stdout = old_stdout


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
            disable_digital(iq)  # 🔥 BLOQUEO TOTAL

            print("BOT ACTIVADO")
            send_message("✅ BOT ACTIVADO")

            return iq

        time.sleep(5)


# ==========================
# SOLO OTC BINARY
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
# TIEMPO EXACTO
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
            return

        if result > 0:
            send_message("✅ WIN")
        else:
            send_message("❌ LOSS")

        return


# ==========================
# EJECUCIÓN
# ==========================
def ejecutar(iq, par, action):

    status, trade_id = silent(
        iq.buy, MONTO, par, action, EXPIRACION
    )

    if not status:
        send_message(f"❌ Rechazada {par}")
        return

    send_message(f"📡 {action.upper()} {par}")

    obtener_resultado(iq, trade_id)


# ==========================
# BOT
# ==========================
def run():

    iq = connect()

    while True:

        esperar_cierre()

        pares = get_otc_abiertos(iq)

        if not pares:
            continue

        print("Analizando...")

        for par in pares:

            candles = silent(
                iq.get_candles, par, TIMEFRAME, 50, time.time()
            )

            if not candles:
                continue

            señal = analyze_market(candles, None, None)

            if not señal:
                continue

            action = señal["action"]

            print(f"SEÑAL {par}")

            esperar_apertura()

            ejecutar(iq, par, action)

            break


if __name__ == "__main__":
    run()
