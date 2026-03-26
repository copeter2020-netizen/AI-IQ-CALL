import os
import time
import sys
from iqoptionapi.stable_api import IQ_Option
from strategy import analyze_market
from telegram_bot import send_message


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


IQ_EMAIL = os.environ.get("IQ_EMAIL")
IQ_PASSWORD = os.environ.get("IQ_PASSWORD")

TIMEFRAME = 60
MONTO = 3550
EXPIRACION = 1


def connect():
    while True:
        iq = IQ_Option(IQ_EMAIL, IQ_PASSWORD)
        silent(iq.connect)

        if iq.check_connect():
            print("✅ Conectado")
            send_message("✅ BOT ACTIVO")
            return iq

        time.sleep(5)


def esperar_cierre():
    while int(time.time()) % 60 != 59:
        time.sleep(0.02)


def esperar_apertura():
    while int(time.time()) % 60 != 0:
        time.sleep(0.001)


def analizar(iq, pair):

    candles = silent(
        iq.get_candles, pair, TIMEFRAME, 40, time.time()
    )

    if not candles:
        return None

    return analyze_market(candles, None, None)


def run():

    iq = connect()

    PAR = "EURUSD-OTC"

    while True:

        esperar_cierre()

        señal = analizar(iq, PAR)

        if not señal:
            print("⚠️ Esperando confirmación estructural...")
            continue

        action = señal["action"]
        score = señal["score"]

        print(f"🎯 {PAR} {action} ({score})")

        esperar_apertura()

        send_message(
            f"📊 {action.upper()} {PAR}\n📈 Confirmación institucional\n⏱ 1m"
        )

        status, trade_id = silent(
            iq.buy, MONTO, PAR, action, EXPIRACION
        )

        if not status:
            send_message("❌ Entrada rechazada")
            continue

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

            break

        if result > 0:
            send_message("✅ WIN")
        else:
            send_message("❌ LOSS")


if __name__ == "__main__":
    run()
