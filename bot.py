import os
import time
from iqoptionapi.stable_api import IQ_Option
from strategy import detectar_trampa
from telegram_bot import send_message

IQ_EMAIL = os.getenv("IQ_EMAIL")
IQ_PASSWORD = os.getenv("IQ_PASSWORD")

PAR = "EURUSD-OTC"
MONTO = 3333.33
EXPIRACION = 1

iq = None


def silent(func, *args, **kwargs):
    try:
        return func(*args, **kwargs)
    except:
        return None


# 🔥 FIX ERROR UNDERLYING (IMPORTANTE)
def fix_api(iq):
    try:
        iq.api.digital_underlying_list = {}
        iq.api.get_digital_underlying_list_data = lambda: {"underlying": []}
        iq.api._IQ_Option__get_digital_open = lambda *args, **kwargs: None
    except:
        pass


def connect():
    global iq

    while True:
        iq = IQ_Option(IQ_EMAIL, IQ_PASSWORD)
        silent(iq.connect)

        if iq.check_connect():
            fix_api(iq)
            print("✅ BOT CONECTADO")
            send_message("✅ BOT ACTIVADO")
            return iq

        print("❌ Reintentando conexión...")
        time.sleep(5)


def esperar_cierre():
    while int(time.time()) % 60 != 59:
        time.sleep(0.02)


def esperar_apertura():
    while int(time.time()) % 60 != 0:
        time.sleep(0.001)


def obtener_resultado(trade_id):

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
            return

        if result > 0:
            send_message("✅ WIN")
        elif result == 0:
            send_message("➖ DRAW")
        else:
            send_message("❌ LOSS")

        return


def ejecutar_trade(accion):

    # 🔁 REINTENTO SI FALLA
    for _ in range(3):

        status, trade_id = silent(
            iq.buy, MONTO, PAR, accion, EXPIRACION
        )

        if status:
            send_message(f"🎯 {accion.upper()} {PAR} (${MONTO})")
            obtener_resultado(trade_id)
            return

        time.sleep(1)

    send_message("⛔ No se pudo ejecutar operación")


def run():

    connect()

    while True:

        esperar_cierre()

        señal = detectar_trampa(iq, PAR)

        if not señal:
            print("⏳ Sin señal...")
            continue

        accion = señal["action"]

        print(f"🎯 Señal: {PAR} {accion}")
        send_message(f"🎯 {PAR} {accion}")

        esperar_apertura()

        ejecutar_trade(accion)


if __name__ == "__main__":
    run()
