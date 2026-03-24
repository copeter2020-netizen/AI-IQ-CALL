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
MONTO = 2545
EXPIRACION = 1

# 🔥 SOLO PARES NORMALES (NO OTC)
PARES = [
    "EURUSD",
    "GBPUSD",
    "USDJPY",
    "AUDUSD",
    "USDCAD",
    "USDCHF",
    "EURGBP",
    "EURJPY"
]


def connect():
    while True:
        iq = IQ_Option(IQ_EMAIL, IQ_PASSWORD)
        silent(iq.connect)
        if iq.check_connect():
            print("✅ Conectado")
            return iq
        time.sleep(5)


def esperar_cierre():
    while int(time.time()) % 60 != 59:
        time.sleep(0.05)


def esperar_apertura():
    while int(time.time()) % 60 != 0:
        time.sleep(0.01)


def contar_color(candles):
    count = 0
    tipo = None

    for i in range(len(candles)-1, -1, -1):
        c = candles[i]

        if c["close"] > c["open"]:
            if tipo in [None, "verde"]:
                tipo = "verde"
                count += 1
            else:
                break
        elif c["close"] < c["open"]:
            if tipo in [None, "roja"]:
                tipo = "roja"
                count += 1
            else:
                break
        else:
            break

    return tipo, count


def analizar(iq, pair):

    candles = silent(
        iq.get_candles, pair, TIMEFRAME, 30, time.time()
    )

    if not candles:
        return None

    tipo, count = contar_color(candles)

    if count < 2 or count > 3:
        return None

    return analyze_market(candles, None, None)


def run():

    iq = connect()

    while True:

        print("⏳ Esperando cierre...")
        esperar_cierre()

        mejor = None
        mejor_pair = None
        mejor_score = 0

        print(f"🔎 Analizando {len(PARES)} pares reales...")

        for pair in PARES:

            señal = analizar(iq, pair)

            if not señal:
                continue

            if señal["score"] > mejor_score:
                mejor_score = señal["score"]
                mejor = señal
                mejor_pair = pair

        if not mejor:
            print("⚠️ Sin señal en pares reales")
            continue

        action = mejor["action"]

        print(f"🎯 {mejor_pair} {action} (score {mejor_score})")

        esperar_apertura()

        send_message(
            f"📊 {action.upper()} {mejor_pair}\n⏱ 1m\n📊 Score: {mejor_score}\n🔥 Mercado real"
        )

        status, trade_id = silent(
            iq.buy, MONTO, mejor_pair, action, EXPIRACION
        )

        if not status:
            continue

        while True:
            result = silent(iq.check_win_v4, trade_id)

            if result is None:
                time.sleep(1)
                continue

            if isinstance(result, tuple):
                result = result[0]

            if isinstance(result, str):
                try:
                    result = float(result)
                except:
                    result = 0

            break

        if result > 0:
            print("✅ WIN")
            send_message("✅ WIN")
        else:
            print("❌ LOSS")
            send_message("❌ LOSS")


if __name__ == "__main__":
    run()
