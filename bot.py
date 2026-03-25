import os
import time
import sys
from iqoptionapi.stable_api import IQ_Option
from strategy import analyze_market
from telegram_bot import send_message


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
MONTO = 1500
EXPIRACION = 1

PAR = "EURUSD-OTC"


# ==========================
# CONEXIÓN
# ==========================
def connect():
    while True:
        iq = IQ_Option(IQ_EMAIL, IQ_PASSWORD)
        silent(iq.connect)

        if iq.check_connect():
            print("✅ Conectado")
            send_message("✅ BOT CONECTADO")
            return iq

        time.sleep(5)


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
# ANALIZAR
# ==========================
def analizar(iq):

    candles = silent(
        iq.get_candles, PAR, TIMEFRAME, 40, time.time()
    )

    if not candles:
        return None

    return analyze_market(candles, None, None)


# ==========================
# EJECUTAR
# ==========================
def ejecutar(iq, action):

    send_message(f"🚀 {action.upper()} {PAR}")

    status, trade_id = silent(
        iq.buy, MONTO, PAR, action, EXPIRACION
    )

    if not status:
        send_message("❌ Broker rechazó")
        return None

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
            result = 0

        return result


# ==========================
# BOT
# ==========================
def run():

    iq = connect()

    while True:

        esperar_cierre()

        señal = analizar(iq)

        if not señal:
            continue

        action = señal["action"]

        send_message(f"📡 SEÑAL {action.upper()}")

        esperar_apertura()

        resultado = ejecutar(iq, action)

        if resultado is None:
            continue

        if resultado > 0:
            send_message("✅ WIN")
        else:
            send_message("❌ LOSS")


if __name__ == "__main__":
    run()
