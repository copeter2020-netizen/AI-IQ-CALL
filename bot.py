import os
import time
from iqoptionapi.stable_api import IQ_Option
from strategy import detectar_trampa
from telegram_bot import send_message


IQ_EMAIL = os.getenv("IQ_EMAIL")
IQ_PASSWORD = os.getenv("IQ_PASSWORD")

MONTO = 10000
EXPIRACION = 1

# 🔥 PARES OTC
PARES = [
    "EURGBP-OTC",
    "GBPUSD-OTC",
    "EURJPY-OTC",
    "USDCHF-OTC",
    "USDIDY-OTC",
    "USDZAR-OTC",
    "USDTRY-OTC",
    "USDTHB-OTC",
    "USDSGD-OTC",
    "USDSEK-OTC",
    "USDPLN-OTC",
    "USDNOK-OTC",
    "USDMXN-OTC",
    "USDINR-OTC",
    "USDHKD-OTC"
]


def silent(func, *args, **kwargs):
    try:
        return func(*args, **kwargs)
    except:
        return None


# 🔥 FIX ERROR UNDERLYING
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
            print("🔥 BOT MULTIPAIRS ACTIVO")
            send_message("🔥 BOT MULTIPAIRS ACTIVO")
            return iq

        time.sleep(5)


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

        if isinstance(result, tuple):
            result = result[0]

        try:
            result = float(result)
        except:
            return

        if result > 0:
            send_message("✅ WIN")
        else:
            send_message("❌ LOSS")

        return


def ejecutar_trade(iq, par, accion):

    status, trade_id = silent(
        iq.buy, MONTO, par, accion, EXPIRACION
    )

    if not status:
        send_message(f"❌ ERROR {par}")
        return False

    send_message(f"📊 {accion.upper()} {par}")

    obtener_resultado(iq, trade_id)

    return True


def run():

    iq = connect()

    while True:

        esperar_cierre()

        print("🔍 Analizando pares...")

        señal_encontrada = False

        for par in PARES:

            señal = detectar_trampa(iq, par)

            if not señal:
                continue

            accion = señal["action"]

            print(f"🎯 {par} {accion}")
            send_message(f"🎯 {accion.upper()} {par}")

            esperar_apertura()

            ejecutado = ejecutar_trade(iq, par, accion)

            if ejecutado:
                señal_encontrada = True
                break

        if not señal_encontrada:
            print("⏳ Sin señales...")


if __name__ == "__main__":
    run()
