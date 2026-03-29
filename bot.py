import os
import time
from iqoptionapi.stable_api import IQ_Option
from strategy import detectar_trampa
from telegram_bot import send_message, start_telegram

IQ_EMAIL = os.getenv("IQ_EMAIL")
IQ_PASSWORD = os.getenv("IQ_PASSWORD")

PAR = "EURUSD-OTC"

# 🔥 VARIABLES DINÁMICAS
MONTO = 3333.33
TIPO_CUENTA = "PRACTICE"  # PRACTICE / REAL

iq = None


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


def conectar():
    global iq

    iq = IQ_Option(IQ_EMAIL, IQ_PASSWORD)
    iq.connect()

    if iq.check_connect():
        fix_api(iq)
        cambiar_cuenta(TIPO_CUENTA)
        print("✅ Conectado")
        send_message("✅ BOT ACTIVO")
        return True

    return False


def cambiar_cuenta(tipo):
    global TIPO_CUENTA
    TIPO_CUENTA = tipo

    if tipo == "REAL":
        iq.change_balance("REAL")
        send_message("🔴 CUENTA REAL")
    else:
        iq.change_balance("PRACTICE")
        send_message("🟢 CUENTA DEMO")


def cambiar_monto(nuevo):
    global MONTO
    MONTO = float(nuevo)
    send_message(f"💰 Nuevo monto: {MONTO}")


def esperar_cierre():
    while int(time.time()) % 60 != 59:
        time.sleep(0.02)


def esperar_apertura():
    while int(time.time()) % 60 != 0:
        time.sleep(0.001)


def resultado(trade_id):

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


def ejecutar(accion):

    status, trade_id = silent(
        iq.buy, MONTO, PAR, accion, 1
    )

    if not status:
        send_message("⛔ Error entrada")
        return

    send_message(f"🎯 {accion.upper()} {PAR} (${MONTO})")

    resultado(trade_id)


def run():

    conectar()

    # 🔥 INICIAR TELEGRAM BOT
    start_telegram(cambiar_cuenta, cambiar_monto)

    while True:

        esperar_cierre()

        señal = detectar_trampa(iq, PAR)

        if not señal:
            print("⏳ Sin señal...")
            continue

        accion = señal["action"]

        send_message(f"🎯 {PAR} {accion}")

        esperar_apertura()

        ejecutar(accion)


if __name__ == "__main__":
    run()
