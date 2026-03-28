import os
import time
from iqoptionapi.stable_api import IQ_Option
from strategy import analizar_vela_apertura
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
            print("✅ BOT ACTIVO (APERTURA)")
            send_message("🚀 BOT ACTIVO - APERTURA")
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


def obtener_resultado(iq, trade_id):

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
            obtener_resultado(iq, trade_id)
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
                iq.get_candles, par, TIMEFRAME, 30, time.time()
            )

            if not candles:
                continue

            señal = analizar_vela_apertura(candles)

            if not señal:
                continue

            if not mejor or señal["score"] > mejor["score"]:
                mejor = señal
                mejor_par = par

        if not mejor:
            print("⏳ Esperando señal apertura...")
            continue

        print(f"🎯 {mejor_par} {mejor['action']}")
        send_message(f"🎯 {mejor_par} {mejor['action']}")

        esperar_apertura()

        # 🔥 ESPERAR RETROCESO BAJO APERTURA
        for _ in range(20):

            candles = silent(
                iq.get_candles, mejor_par, TIMEFRAME, 1, time.time()
            )

            if not candles:
                continue

            vela = candles[-1]

            if vela["close"] < vela["open"]:
                ejecutar(iq, mejor_par, mejor["action"])
                break

            time.sleep(1)


if __name__ == "__main__":
    run()
