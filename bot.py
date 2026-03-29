import os
import time
from iqoptionapi.stable_api import IQ_Option
from strategy import detectar_trampa
from telegram_bot import send_message

IQ_EMAIL = os.getenv("IQ_EMAIL")
IQ_PASSWORD = os.getenv("IQ_PASSWORD")

PAR = "EURUSD-OTC"
MONTO = 100
EXPIRACION = 1


def silent(func, *args, **kwargs):
    try:
        return func(*args, **kwargs)
    except:
        return None


# 🔥 FIX ERROR UNDERLYING (OBLIGATORIO)
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
            print("✅ BOT CONECTADO")
            send_message("✅ BOT CONECTADO")
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


def ejecutar_trade(iq, accion):

    status, trade_id = silent(
        iq.buy, MONTO, PAR, accion, EXPIRACION
    )

    if not status:
        send_message("❌ ERROR ENTRADA")
        return

    send_message(f"📊 {accion.upper()} {PAR}")

    obtener_resultado(iq, trade_id)


def run():

    iq = connect()

    while True:

        esperar_cierre()

        # 🔥 USO EXACTO DE LA ESTRATEGIA
        señal = detectar_trampa(iq, PAR)

        if not señal:
            print("⏳ Sin señal...")
            continue

        accion = señal["action"]

        print(f"🎯 SEÑAL {accion} {PAR}")
        send_message(f"🎯 {accion.upper()} {PAR}")

        esperar_apertura()

        ejecutar_trade(iq, accion)


if __name__ == "__main__":
    run()import os
import time
from iqoptionapi.stable_api import IQ_Option
from strategy import detectar_trampa
from telegram_bot import send_message

IQ_EMAIL = os.getenv("IQ_EMAIL")
IQ_PASSWORD = os.getenv("IQ_PASSWORD")

PAR = "EURUSD-OTC"
MONTO = 10
EXPIRACION = 1


def silent(func, *args, **kwargs):
    try:
        return func(*args, **kwargs)
    except:
        return None


# 🔥 FIX ERROR UNDERLYING (OBLIGATORIO)
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
            print("✅ BOT CONECTADO")
            send_message("✅ BOT CONECTADO")
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


def ejecutar_trade(iq, accion):

    status, trade_id = silent(
        iq.buy, MONTO, PAR, accion, EXPIRACION
    )

    if not status:
        send_message("❌ ERROR ENTRADA")
        return

    send_message(f"📊 {accion.upper()} {PAR}")

    obtener_resultado(iq, trade_id)


def run():

    iq = connect()

    while True:

        esperar_cierre()

        # 🔥 USO EXACTO DE LA ESTRATEGIA
        señal = detectar_trampa(iq, PAR)

        if not señal:
            print("⏳ Sin señal...")
            continue

        accion = señal["action"]

        print(f"🎯 SEÑAL {accion} {PAR}")
        send_message(f"🎯 {accion.upper()} {PAR}")

        esperar_apertura()

        ejecutar_trade(iq, accion)


if __name__ == "__main__":
    run()
