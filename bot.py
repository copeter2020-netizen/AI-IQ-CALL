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
MONTO = 65
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


# ==========================
# 🔥 OBTENER TODOS LOS OTC ABIERTOS
# ==========================
def get_otc_abiertos(iq):

    try:
        activos = iq.get_all_open_time()
        pares = []

        for par, data in activos["binary"].items():

            if "-OTC" in par and data["open"]:
                pares.append(par)

        return pares

    except:
        return []


def esperar_cierre():
    while int(time.time()) % 60 != 59:
        time.sleep(0.02)


def esperar_apertura():
    while int(time.time()) % 60 != 0:
        time.sleep(0.001)


def analizar_par(iq, pair):

    candles = silent(
        iq.get_candles, pair, TIMEFRAME, 10, time.time()
    )

    if not candles:
        return None

    return analyze_market(candles, None, None)


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

    send_message(f"📊 CALL {pair}\n⏱ 1m\n🔥 2da vela verde")

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

        señales = []

        for par in pares:

            señal = analizar_par(iq, par)

            if señal:
                señales.append((par, señal))

        if not señales:
            print("⚠️ Sin señales...")
            continue

        par, señal = señales[0]

        print(f"🎯 {par} CALL → 2da vela verde")

        esperar_apertura()

        ejecutar_trade(iq, par, "call")


if __name__ == "__main__":
    run()
