import os
import time
from iqoptionapi.stable_api import IQ_Option
from strategy import detectar_trampa
from telegram_bot import send_message

IQ_EMAIL = os.getenv("IQ_EMAIL")
IQ_PASSWORD = os.getenv("IQ_PASSWORD")

# 🔥 MULTIPARES (corregido)
PARES = [
    
    "EURUSD-OTC",
    "GBPUSD-OTC",
    "EURAUD-OTC",
    "CHFNOK-OTC",
    "CHFJPY-OTC",
    "CADJPY-OTC",
    "CADCHF-OTC",
    "AUDUSD-OTC",
    "AUDNZD-OTC",
    "AUDJPY-OTC",
    "AUDCHF-OTC",
    "AUDCAD-OTC",
    "GBPCHF-OTC",
    "GBPCAD-OTC",
    "GBPAUD-OTC",
    "EURUSD-OTC",
    "EURTHB-OTC",
    "EURNZD-OTC",
    "EURJPY-OTC",
    "EURGBP-OTC",
    "EURCHF-OTC",
    "USDCHF-OTC",
    "USDCAD-OTC",
    "USDBRL-OTC",
    "PENUSD-OTC",
    "NZDJPY-OTC",
    "NZDCAD-OTC",
    "NOKJPY-OTC",
    "JPYTHB-OTC",
    "GBPUSD-OTC",
    "GBPNZD-OTC",
    "GBPJPY-OTC", 
    "EURJPY-OTC",
    "USDHKD-OTC",
    "EURGBP-OTC"
]

MONTO = 150
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
        return True


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


def ejecutar(iq, par, accion):

    for _ in range(3):
        status, trade_id = silent(
            iq.buy, MONTO, par, accion, EXPIRACION
        )

        if status:
            send_message(f"🎯 {accion.upper()} {par} ({EXPIRACION}M)")
            resultado(iq, trade_id)
            return

        time.sleep(1)

    send_message(f"⛔ No ejecutó operación en {par}")


def run():

    iq = connect()

    while True:

        if not estado_bot():
            print("⛔ BOT DETENIDO")
            time.sleep(2)
            continue

        esperar_cierre()

        for par in PARES:

            señal = detectar_trampa(iq, par)

            if not señal:
                continue

            accion = señal["action"]

            print(f"🎯 {par} {accion}")
            send_message(f"🎯 {par} {accion}")

            esperar_apertura()

            ejecutar(iq, par, accion)

            break  # SOLO UNA OPERACIÓN POR VELA


if __name__ == "__main__":
    run()
