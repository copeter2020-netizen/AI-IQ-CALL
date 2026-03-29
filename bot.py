import os
import time
from iqoptionapi.stable_api import IQ_Option
from strategy import detectar_trampa
from telegram_bot import send_message


IQ_EMAIL = os.getenv("IQ_EMAIL")
IQ_PASSWORD = os.getenv("IQ_PASSWORD")

MONTO = 3333.33
EXPIRACION = 1

PARES = [
    "EURUSD-OTC",
    "EURGBP-OTC",
    "GBPUSD-OTC",
    "EURJPY-OTC",
    "USDCHF-OTC"
]


def silent(func, *args, **kwargs):
    try:
        return func(*args, **kwargs)
    except:
        return None


def fix_api(iq):
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
            fix_api(iq)
            print("🔥 BOT INDICADORES ACTIVO")
            send_message("🔥 BOT INDICADORES ACTIVO")
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

        if isinstance(r, tuple):
            r = r[0]

        try:
            r = float(r)
        except:
            return

        send_message("✅ WIN" if r > 0 else "❌ LOSS")
        return


def ejecutar(iq, par, accion):

    status, trade_id = silent(
        iq.buy, MONTO, par, accion, EXPIRACION
    )

    if not status:
        send_message(f"❌ ERROR {par}")
        return

    send_message(f"📊 {accion.upper()} {par}")

    resultado(iq, trade_id)


def run():

    iq = connect()

    while True:

        esperar_cierre()

        print("🔍 Analizando...")

        for par in PARES:

            señal = detectar_trampa(iq, par)

            if not señal:
                continue

            accion = señal["action"]

            print(f"🎯 {par} {accion}")
            send_message(f"🎯 {accion.upper()} {par}")

            esperar_apertura()

            ejecutar(iq, par, accion)

            break


if __name__ == "__main__":
    run()
