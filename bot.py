import os
import time
from iqoptionapi.stable_api import IQ_Option
from strategy import detectar_trampa
from telegram_bot import send_message

IQ_EMAIL = os.getenv("IQ_EMAIL")
IQ_PASSWORD = os.getenv("IQ_PASSWORD")

MONTO = 12000
EXPIRACION = 1


# 🔥 SOLO FOREX OTC REALES (CLAVE DEL FIX)
PARES_VALIDOS = [
    "EURUSD-OTC","GBPUSD-OTC","USDJPY-OTC","USDCHF-OTC",
    "AUDUSD-OTC","USDCAD-OTC","NZDUSD-OTC",
    "EURGBP-OTC","EURJPY-OTC","GBPJPY-OTC",
    "AUDJPY-OTC","CHFJPY-OTC","EURAUD-OTC",
    "GBPAUD-OTC","EURCAD-OTC","AUDCAD-OTC"
]


def silent(func, *args, **kwargs):
    try:
        return func(*args, **kwargs)
    except:
        return None


def connect():
    while True:
        iq = IQ_Option(IQ_EMAIL, IQ_PASSWORD)
        silent(iq.connect)

        if iq.check_connect():
            print("🔥 BOT ACTIVO SIN ERRORES")
            send_message("🔥 BOT ACTIVO SIN ERRORES")
            return iq

        time.sleep(3)


def esperar_cierre():
    while int(time.time()) % 60 != 59:
        time.sleep(0.05)
    time.sleep(1)


def esperar_apertura():
    while int(time.time()) % 60 != 0:
        time.sleep(0.01)
    time.sleep(0.2)


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
            print("WIN")
            send_message("✅ WIN")
        else:
            print("LOSS")
            send_message("❌ LOSS")

        return


def ejecutar(iq, par, accion):

    # 🔥 INVERTIDO
    accion = "put" if accion == "call" else "call"

    print(f"ENTRADA: {accion.upper()} {par}")
    send_message(f"🚨 {accion.upper()} {par}")

    status, trade_id = silent(
        iq.buy, MONTO, par, accion, EXPIRACION
    )

    if status:
        resultado(iq, trade_id)


def run():

    iq = connect()

    while True:

        esperar_cierre()

        for par in PARES_VALIDOS:

            señal = detectar_trampa(iq, par)

            if señal:
                print(f"SEÑAL: {par} {señal['action']}")
                send_message(f"🎯 SEÑAL {par}")

                esperar_apertura()
                ejecutar(iq, par, señal["action"])
                break


if __name__ == "__main__":
    run()
