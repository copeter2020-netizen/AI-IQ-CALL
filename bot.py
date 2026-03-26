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
MONTO = 6000
EXPIRACION = 1  # 🔥 SOLO 1 MINUTO


# 🔥 9 PARES (BINARIAS OTC 1 MIN)
PARES = [
    "EURUSD-OTC",
    "GBPUSD-OTC",
    "USDJPY-OTC",
    "AUDUSD-OTC",
    "USDCAD-OTC",
    "EURGBP-OTC",
    "EURJPY-OTC",
    "GBPJPY-OTC",
    "AUDJPY-OTC"
]


def connect():
    while True:
        iq = IQ_Option(IQ_EMAIL, IQ_PASSWORD)
        silent(iq.connect)

        if iq.check_connect():
            print("✅ Conectado")
            send_message("✅ BOT ACTIVO 1M MULTIPAIR")
            return iq

        time.sleep(5)


def esperar_cierre():
    while int(time.time()) % 60 != 59:
        time.sleep(0.02)


def esperar_apertura():
    while int(time.time()) % 60 != 0:
        time.sleep(0.001)


def analizar_par(iq, pair):

    candles = silent(
        iq.get_candles, pair, TIMEFRAME, 40, time.time()
    )

    if not candles:
        return None

    return analyze_market(candles, None, None)


def ejecutar_trade(iq, pair, action):

    status, trade_id = silent(
        iq.buy, MONTO, pair, action, EXPIRACION
    )

    if not status:
        send_message(f"❌ Entrada rechazada {pair}")
        return

    send_message(
        f"📊 {action.upper()} {pair}\n⏱ 1m\n💰 {MONTO}"
    )

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
        send_message(f"✅ WIN {pair}")
    else:
        send_message(f"❌ LOSS {pair}")


def run():

    iq = connect()

    while True:

        esperar_cierre()

        señales = []

        # 🔍 ANALIZAR LOS 9 PARES
        for par in PARES:

            señal = analizar_par(iq, par)

            if señal:
                señales.append((par, señal))

        if not señales:
            print("⚠️ Sin señales...")
            continue

        # 🔥 PRIMERA SEÑAL DETECTADA
        par, señal = señales[0]

        action = señal["action"]

        print(f"🎯 {par} {action}")

        esperar_apertura()

        ejecutar_trade(iq, par, action)


if __name__ == "__main__":
    run()
