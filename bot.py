import os
import time
from iqoptionapi.stable_api import IQ_Option
from strategy import analizar_institucional
from telegram_bot import send_message


IQ_EMAIL = os.getenv("IQ_EMAIL")
IQ_PASSWORD = os.getenv("IQ_PASSWORD")

TIMEFRAME = 60
MONTO = 3330
EXPIRACION = 1

PARES = [
    "EURUSD-OTC",
    "GBPUSD-OTC",
    "EURGBP-OTC",
    "EURJPY-OTC",
    "USDCHF-OTC"
]

bloqueados = set()


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
            print("🔥 SNIPER INSTITUCIONAL ACTIVO")
            send_message("🔥 SNIPER INSTITUCIONAL ACTIVADO")
            return iq

        time.sleep(5)


def pares_abiertos(iq):
    try:
        data = iq.get_all_open_time()
        return [
            p for p in PARES
            if data["binary"][p]["open"] and p not in bloqueados
        ]
    except:
        return []


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

        mejor = None
        mejor_par = None

        for par in pares:

            candles = silent(
                iq.get_candles, par, TIMEFRAME, 50, time.time()
            )

            if not candles:
                continue

            señal = analizar_institucional(candles)

            if not señal:
                continue

            if not mejor or señal["score"] > mejor["score"]:
                mejor = señal
                mejor_par = par

        if not mejor:
            print("⏳ Esperando manipulación...")
            continue

        print(f"🎯 {mejor_par} {mejor['action']}")
        send_message(f"🎯 SNIPER {mejor_par} {mejor['action']}")

        esperar_apertura()

        # 🔥 ENTRADA EN RETROCESO (SMART MONEY)
        for _ in range(25):

            vela = silent(
                iq.get_candles, mejor_par, TIMEFRAME, 1, time.time()
            )

            if not vela:
                continue

            vela = vela[-1]

            if mejor["action"] == "call":
                if vela["close"] < vela["open"]:
                    ejecutar(iq, mejor_par, "call")
                    break

            if mejor["action"] == "put":
                if vela["close"] > vela["open"]:
                    ejecutar(iq, mejor_par, "put")
                    break

            time.sleep(1)


if __name__ == "__main__":
    run()
