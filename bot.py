import os
import time
from iqoptionapi.stable_api import IQ_Option
from strategy import detectar_entrada
from telegram_bot import send_message

IQ_EMAIL = os.getenv("IQ_EMAIL")
IQ_PASSWORD = os.getenv("IQ_PASSWORD")

MONTO = 2000
EXPIRACION = 1


def safe(func, *args, **kwargs):
    try:
        return func(*args, **kwargs)
    except:
        return None


def connect():
    while True:
        iq = IQ_Option(IQ_EMAIL, IQ_PASSWORD)
        safe(iq.connect)

        if iq.check_connect():
            print("BOT ACTIVADO")
            send_message("🔥 BOT OPERANDO")
            return iq

        time.sleep(3)


def esperar_cierre():
    while int(time.time()) % 60 != 59:
        time.sleep(0.03)


def esperar_apertura():
    while int(time.time()) % 60 != 0:
        time.sleep(0.005)


# 🔥 SOLO PARES REALES OPERABLES
def obtener_pares(iq):
    try:
        activos = iq.get_all_ACTIVES_OPCODE()
        return [par for par in activos.keys() if "-OTC" in par]
    except:
        return []


# 🔥 EJECUCIÓN REAL
def ejecutar(iq, par, accion):

    try:
        status, trade_id = iq.buy_digital_spot(
            par,
            MONTO,
            accion,
            EXPIRACION
        )
    except:
        return

    if status:
        print(f"ENTRADA: {accion.upper()} {par}")
        send_message(f"🎯 ENTRADA {accion.upper()} {par}")


def run():

    iq = connect()

    while True:

        esperar_cierre()

        pares = obtener_pares(iq)

        if not pares:
            continue

        for par in pares:

            señal = detectar_entrada(iq, par)

            if señal:

                accion = señal["action"]

                print(f"SEÑAL: {par} {accion}")
                send_message(f"🚨 {par} {accion}")

                esperar_apertura()
                ejecutar(iq, par, accion)

                break


if __name__ == "__main__":
    run()
