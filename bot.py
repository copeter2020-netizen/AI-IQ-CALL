import os
import time
import sys
from iqoptionapi.stable_api import IQ_Option
from strategy import analizar_macd_price_action
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


IQ_EMAIL = os.getenv("IQ_EMAIL")
IQ_PASSWORD = os.getenv("IQ_PASSWORD")

PAR = "EURUSD-OTC"
TIMEFRAME = 60
MONTO = 7500
EXPIRACION = 1


def connect():
    while True:
        iq = IQ_Option(IQ_EMAIL, IQ_PASSWORD)

        silent(iq.connect)

        if iq.check_connect():

            # 🔥 BLOQUEAR DIGITALES (SOLUCIÓN REAL)
            try:
                iq.api.digital_underlying_list = {}
                iq.api.get_digital_underlying_list_data = lambda: {}
            except:
                pass

            print("✅ BOT SIN ERROR UNDERLYING")
            send_message("✅ BOT ACTIVO EURUSD SNIPER")

            return iq

        time.sleep(5)


def par_abierto(iq):
    try:
        data = iq.get_all_open_time()
        return data["binary"][PAR]["open"]
    except:
        return False


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

        if r > 0:
            send_message("✅ WIN EURUSD")
        else:
            send_message("❌ LOSS EURUSD")

        return


def ejecutar(iq, accion):

    for _ in range(3):

        status, trade_id = silent(
            iq.buy, MONTO, PAR, accion, EXPIRACION
        )

        if status:
            print(f"🚀 {PAR} {accion}")
            send_message(f"📊 {accion.upper()} {PAR}")
            resultado(iq, trade_id)
            return

        time.sleep(0.5)

    send_message("⛔ Error entrada EURUSD")


def run():

    iq = connect()

    while True:

        if not par_abierto(iq):
            print("⛔ EURUSD cerrado")
            time.sleep(5)
            continue

        esperar_cierre()

        candles = silent(
            iq.get_candles, PAR, TIMEFRAME, 60, time.time()
        )

        if not candles:
            continue

        señal = analizar_macd_price_action(candles)

        if not señal:
            print("🎯 SNIPER esperando...")
            continue

        print(f"🎯 EURUSD {señal['action']}")
        send_message(f"🎯 EURUSD {señal['action']}")

        esperar_apertura()

        ejecutar(iq, señal["action"])


if __name__ == "__main__":
    run()
