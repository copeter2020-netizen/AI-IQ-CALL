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
    try:
        return func(*args, **kwargs)
    except:
        return None


IQ_EMAIL = os.getenv("IQ_EMAIL")
IQ_PASSWORD = os.getenv("IQ_PASSWORD")

TIMEFRAME = 60
MONTO = 7550
EXPIRACION = 1

# 🔥 PARES OTC
PARES = [
    "EURUSD-OTC",
    "GBPUSD-OTC",
    "EURGBP-OTC",
    "EURJPY-OTC",
    "USDCHF-OTC"
]

bloqueados = set()


# ==========================
# 🔥 FIX UNDERLYING DEFINITIVO
# ==========================
def fix_underlying_bug(iq):
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

            fix_underlying_bug(iq)

            print("✅ BOT MULTI-PAR SNIPER")
            send_message("🚀 BOT MULTI-PAR ACTIVADO")

            return iq

        time.sleep(5)


def pares_abiertos(iq):
    abiertos = []
    try:
        data = iq.get_all_open_time()

        for par in PARES:
            if data["binary"][par]["open"] and par not in bloqueados:
                abiertos.append(par)

    except:
        pass

    return abiertos


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
            send_message("✅ WIN")
        else:
            send_message("❌ LOSS")

        return


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

        time.sleep(0.5)

    bloqueados.add(par)
    send_message(f"⛔ {par} bloqueado")
    return False


def run():

    iq = connect()

    while True:

        esperar_cierre()

        pares = pares_abiertos(iq)

        if not pares:
            print("⚠️ Sin pares abiertos")
            continue

        mejor = None
        mejor_par = None

        for par in pares:

            candles = silent(
                iq.get_candles, par, TIMEFRAME, 60, time.time()
            )

            if not candles:
                continue

            señal = analizar_macd_price_action(candles)

            if not señal:
                continue

            # 🔥 SNIPER → solo lo mejor
            if señal["score"] >= 5:
                if not mejor or señal["score"] > mejor["score"]:
                    mejor = señal
                    mejor_par = par

        if not mejor:
            print("🎯 SNIPER esperando...")
            continue

        print(f"🎯 {mejor_par} {mejor['action']}")
        send_message(f"🎯 {mejor_par} {mejor['action']}")

        esperar_apertura()

        ejecutar(iq, mejor_par, mejor["action"])


if __name__ == "__main__":
    run()
