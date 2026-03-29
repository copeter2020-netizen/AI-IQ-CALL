import os
import time
from iqoptionapi.stable_api import IQ_Option
from strategy import detectar_trampa
from telegram_bot import send_message

IQ_EMAIL = os.getenv("IQ_EMAIL")
IQ_PASSWORD = os.getenv("IQ_PASSWORD")

PAR = "EURUSD-OTC"
MONTO = 3333.38
EXPIRACION = 1

CONTROL_FILE = "estado.txt"


def silent(func, *args, **kwargs):
    try:
        return func(*args, **kwargs)
    except:
        return None


def fix_api(iq):
    try:
        iq.api.digital_underlying_list = {}
        iq.api.get_digital_underlying_list_data = lambda: {"underlying": []}
        iq.api._IQ_Option__get_digital_open = lambda *args, **kwargs: None
    except:
        pass


def estado_bot():
    try:
        with open(CONTROL_FILE, "r") as f:
            estado = f.read().strip().upper()
            return estado == "ON"
    except:
        return True  # por defecto encendido


def connect():
    while True:
        iq = IQ_Option(IQ_EMAIL, IQ_PASSWORD)
        silent(iq.connect)

        if iq.check_connect():
            fix_api(iq)
            print("🔥 BOT ACTIVO")
            send_message("🔥 BOT ACTIVO")
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

        try:
            if isinstance(r, tuple):
                r = r[0]
            r = float(r)
        except:
            return

        send_message("✅ WIN" if r > 0 else "❌ LOSS")
        return


def ejecutar(iq, accion):

    for _ in range(3):
        status, trade_id = silent(
            iq.buy, MONTO, PAR, accion, EXPIRACION
        )

        if status:
            send_message(f"🎯 {accion.upper()} {PAR} (1M)")
            resultado(iq, trade_id)
            return

        time.sleep(1)

    send_message("⛔ No ejecutó operación")


def run():

    iq = connect()

    while True:

        # 🔴 BOT APAGADO
        if not estado_bot():
            print("⛔ BOT DETENIDO")
            time.sleep(2)
            continue

        esperar_cierre()

        señal = detectar_trampa(iq, PAR)

        if not señal:
            print("⏳ Sin señal...")
            continue

        accion = señal["action"]

        print(f"🎯 {PAR} {accion}")
        send_message(f"🎯 {PAR} {accion}")

        esperar_apertura()

        ejecutar(iq, accion)


if __name__ == "__main__":
    run()
