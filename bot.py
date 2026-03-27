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
MONTO = 78
EXPIRACION = 1


def connect():
    while True:
        iq = IQ_Option(IQ_EMAIL, IQ_PASSWORD)
        silent(iq.connect)

        if iq.check_connect():
            print("✅ Conectado")
            send_message("✅ BOT SMART MONEY ACTIVO")
            return iq

        time.sleep(5)


def get_otc_abiertos(iq):
    try:
        activos = iq.get_all_open_time()
        return [
            par for par, data in activos["binary"].items()
            if "-OTC" in par and data["open"]
        ]
    except:
        return []


def esperar_cierre():
    while int(time.time()) % 60 != 59:
        time.sleep(0.02)


def esperar_apertura():
    while int(time.time()) % 60 != 0:
        time.sleep(0.001)


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


def ejecutar_trade(iq, pair, action):

    status, trade_id = silent(
        iq.buy, MONTO, pair, action, EXPIRACION
    )

    if not status:
        send_message(f"❌ Entrada rechazada {pair}")
        return

    send_message(f"📊 {action.upper()} {pair}\n🧠 Contra Smart Money")

    resultado = obtener_resultado(iq, trade_id)

    if resultado == "win":
        send_message(f"✅ WIN {pair}")
    elif resultado == "draw":
        send_message(f"➖ DRAW {pair}")
    else:
        send_message(f"❌ LOSS {pair}")


def run():

    iq = connect()

    while True:

        esperar_cierre()

        pares = get_otc_abiertos(iq)

        if not pares:
            print("⚠️ No hay OTC abiertos")
            continue

        for par in pares:

            candles = silent(
                iq.get_candles, par, TIMEFRAME, 20, time.time()
            )

            if not candles:
                continue

            señal = analyze_market(candles, None, None)

            if not señal:
                continue

            action = señal["action"]

            print(f"🎯 {par} {action} → smart money detectado")

            esperar_apertura()

            ejecutar_trade(iq, par, action)

            break
        else:
            print("⚠️ Sin manipulaciones detectadas...")


if __name__ == "__main__":
    run()
