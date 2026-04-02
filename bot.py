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
MONTO = 20000
EXPIRACION = 1

MAX_PARES = 25  # 🔥 VELOCIDAD

BLACKLIST = ["USDJPY", "USDSGD", "NZDUSD"]


# ==========================
# CONEXIÓN
# ==========================
def connect():
    while True:
        iq = IQ_Option(IQ_EMAIL, IQ_PASSWORD)

        silent(iq.connect)

        if iq.check_connect():
            print("✅ Conectado")
            silent(iq.get_all_open_time)
            return iq
        else:
            time.sleep(5)


# ==========================
# FILTRAR PARES
# ==========================
def get_pairs(iq):

    pairs = []

    assets = silent(iq.get_all_open_time)

    if not assets or "binary" not in assets:
        return []

    for par in assets["binary"]:
        try:
            if assets["binary"][par]["open"] and "-OTC" in par:

                limpio = par.replace("-OTC", "").replace("/", "")

                if limpio in BLACKLIST:
                    continue

                pairs.append(par)

        except:
            continue

    return pairs[:MAX_PARES]  # 🔥 SOLO LOS MEJORES


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
def analizar(iq, pair):

    candles = silent(
        iq.get_candles, pair, TIMEFRAME, 30, time.time()
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

        pairs = get_pairs(iq)

        mejor = None
        mejor_pair = None
        mejor_score = 0

        print(f"🔎 Analizando {len(pairs)} pares...")

        for pair in pairs:

            señal = analizar(iq, pair)

            if not señal:
                continue

            if señal["score"] > mejor_score:
                mejor_score = señal["score"]
                mejor = señal
                mejor_pair = pair

        if not mejor:
            print("❌ Sin entrada válida")
            continue

        print(f"🎯 {mejor_pair} (score {mejor_score:.2f})")

        esperar_apertura()

        send_message(f"🎯 {mejor_pair}\nVENTA\n⏱ 1m")

        status, trade_id = silent(
            iq.buy, MONTO, mejor_pair, "put", EXPIRACION
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
