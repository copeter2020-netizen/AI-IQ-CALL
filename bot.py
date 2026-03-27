import os
import time
import sys
from iqoptionapi.stable_api import IQ_Option
from strategy import analizar_price_action
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

TIMEFRAME = 60
MONTO = 1750
EXPIRACION = 1

bloqueados = set()


# ==========================
# CONEXIÓN
# ==========================
def connect():
    while True:
        iq = IQ_Option(IQ_EMAIL, IQ_PASSWORD)
        silent(iq.connect)

        if iq.check_connect():

            # 🔥 FIX ERROR UNDERLYING
            try:
                iq.api.digital_underlying_list = {}
            except:
                pass

            print("✅ BOT ACTIVADO")
            send_message("✅ BOT ACTIVADO")
            return iq

        time.sleep(5)


# ==========================
# PARES
# ==========================
def get_pairs(iq):
    try:
        data = iq.get_all_open_time()

        return [
            p for p, d in data["binary"].items()
            if "-OTC" in p and d["open"] and p not in bloqueados
        ]
    except:
        return []


def esperar_cierre():
    while int(time.time()) % 60 != 59:
        time.sleep(0.02)


def esperar_apertura():
    while int(time.time()) % 60 != 0:
        time.sleep(0.001)


# ==========================
# RESULTADO
# ==========================
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
            send_message("✅ WIN")
        else:
            send_message("❌ LOSS")

        return


# ==========================
# EJECUCIÓN
# ==========================
def ejecutar(iq, par, accion):

    for _ in range(3):

        status, trade_id = silent(
            iq.buy, MONTO, par, accion, EXPIRACION
        )

        if status:
            print(f"🚀 {par} {accion}")
            send_message(f"📊 {accion.upper()} {par}")
            resultado(iq, trade_id)
            return True

        time.sleep(0.3)

    bloqueados.add(par)
    send_message(f"⛔ {par} bloqueado")
    return False


# ==========================
# BOT
# ==========================
def run():

    iq = connect()

    while True:

        esperar_cierre()

        pares = get_pairs(iq)

        if not pares:
            print("⚠️ Sin pares")
            continue

        print(f"🔎 Analizando {len(pares)} pares...")

        mejor_par = None
        mejor = None

        for par in pares:

            candles = silent(
                iq.get_candles, par, TIMEFRAME, 30, time.time()
            )

            if not candles:
                continue

            señal = analizar_price_action(candles)

            if not señal:
                continue

            if not mejor or señal["score"] > mejor["score"]:
                mejor = señal
                mejor_par = par

        if not mejor:
            print("⚠️ Sin señal")
            continue

        print(f"🎯 {mejor_par} {mejor['action']} ({mejor['score']})")
        send_message(f"🎯 {mejor_par} {mejor['action']}")

        esperar_apertura()

        ejecutar(iq, mejor_par, mejor["action"])


if __name__ == "__main__":
    run()
