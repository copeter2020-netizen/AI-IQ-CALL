import os
import time
import sys
from iqoptionapi.stable_api import IQ_Option
from strategy import analyze_market
from telegram_bot import send_message


# ==========================
# SILENCIAR LOGS
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
IQ_EMAIL = os.environ.get("IQ_EMAIL")
IQ_PASSWORD = os.environ.get("IQ_PASSWORD")

TIMEFRAME = 60
MONTO = 2545
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
            return iq
        else:
            time.sleep(5)


# ==========================
# TIEMPO
# ==========================
def esperar_cierre():
    while int(time.time()) % 60 != 59:
        time.sleep(0.05)


def esperar_apertura():
    while int(time.time()) % 60 != 0:
        time.sleep(0.01)


# ==========================
# ANALIZAR
# ==========================
def analizar(iq):

    candles = silent(
        iq.get_candles, PAR, TIMEFRAME, 30, time.time()
    )

    if not candles:
        return None

    return analyze_market(candles, None, None)


# ==========================
# BOT PRINCIPAL
# ==========================
def run():

    iq = connect()

    while True:

        print("⏳ Esperando cierre...")
        esperar_cierre()

        señal = analizar(iq)

        if not señal:
            print("⚠️ Esperando continuidad alcista real...")
            continue

        score = señal["score"]

        print(f"🎯 {PAR} (score {score})")

        esperar_apertura()

        send_message(
            f"📈 CALL {PAR}\n⏱ 1m\n📊 Score: {score}\n📍 Max: {señal['maximo']}\n📍 Min: {señal['minimo']}\n🔥 Continuidad confirmada"
        )

        status, trade_id = silent(
            iq.buy, MONTO, PAR, "call", EXPIRACION
        )

        if not status:
            continue

        while True:
            result = silent(iq.check_win_v4, trade_id)
            if result is not None:
                break
            time.sleep(1)

        if result > 0:
            print("✅ WIN")
            send_message("✅ WIN")
        else:
            print("❌ LOSS")
            send_message("❌ LOSS")


if __name__ == "__main__":
    run()
