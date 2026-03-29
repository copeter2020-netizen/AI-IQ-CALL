import os
import time
from iqoptionapi.stable_api import IQ_Option
from strategy import detectar_reversion_extrema
from telegram_bot import send_message

IQ_EMAIL = os.getenv("IQ_EMAIL")
IQ_PASSWORD = os.getenv("IQ_PASSWORD")

PAR = "EURUSD-OTC"
TIMEFRAME = 60
MONTO = 10000
EXPIRACION = 1


def silent(func, *args, **kwargs):
    try:
        return func(*args, **kwargs)
    except:
        return None


# 🔥 FIX ERROR UNDERLYING
def fix_underlying(iq):
    try:
        iq.api.digital_underlying_list = {}
        iq.api.get_digital_underlying_list_data = lambda: {}
        iq.api._IQ_Option__get_digital_open = lambda *args, **kwargs: None
    except:
        pass


def connect():
    while True:
        iq = IQ_Option(IQ_EMAIL, IQ_PASSWORD)
        silent(iq.connect)

        if iq.check_connect():
            fix_underlying(iq)
            print("🔥 BOT REVERSIÓN EXTREMA ACTIVO")
            send_message("🔥 BOT REVERSIÓN EXTREMA ACTIVO")
            return iq

        time.sleep(5)


def esperar_cierre():
    while int(time.time()) % 60 != 59:
        time.sleep(0.02)


def esperar_apertura():
    while int(time.time()) % 60 != 0:
        time.sleep(0.001)


def resultado(iq, trade_id):
    while True:
        r = silent(iq.check_win_v4, trade_id)

        if r is None:
            time.sleep(1)
            continue

        try:
            if isinstance(r, tuple):
                r = r[0]
            r = float(r)
        except:
            return

        send_message("✅ WIN" if r > 0 else "❌ LOSS")
        return


def ejecutar(iq, accion):

    for _ in range(3):
        status, trade_id = silent(
            iq.buy, MONTO, PAR, accion, EXPIRACION
        )

        if status:
            send_message(f"📊 {accion.upper()} EURUSD")
            resultado(iq, trade_id)
            return

        time.sleep(0.5)

    send_message("⛔ Error entrada")


def run():

    iq = connect()

    while True:

        esperar_cierre()

        candles = silent(
            iq.get_candles, PAR, TIMEFRAME, 50, time.time()
        )

        if not candles:
            continue

        señal = detectar_reversion_extrema(candles)

        if not señal:
            print("⏳ Esperando señal...")
            continue

        print(f"🎯 EURUSD {señal['action']}")
        send_message(f"🎯 EURUSD {señal['action']}")

        esperar_apertura()

        # 🔥 ENTRADA EN RETROCESO
        for _ in range(25):

            vela = silent(
                iq.get_candles, PAR, TIMEFRAME, 1, time.time()
            )

            if not vela:
                continue

            vela = vela[-1]

            if señal["action"] == "call":
                if vela["close"] < vela["open"]:
                    ejecutar(iq, "call")
                    break

            if señal["action"] == "put":
                if vela["close"] > vela["open"]:
                    ejecutar(iq, "put")
                    break

            time.sleep(1)


if __name__ == "__main__":
    run()
