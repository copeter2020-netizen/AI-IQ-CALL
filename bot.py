import os
import time
from iqoptionapi.stable_api import IQ_Option
from strategy import detectar_entrada
from telegram_bot import send_message

IQ_EMAIL = os.getenv("IQ_EMAIL")
IQ_PASSWORD = os.getenv("IQ_PASSWORD")

MONTO = 2000
EXPIRACION = 1


def connect():
    while True:
        iq = IQ_Option(IQ_EMAIL, IQ_PASSWORD)
        iq.connect()

        if iq.check_connect():
            print("BOT ACTIVADO")
            send_message("🔥 BOT PRICE ACTION ACTIVO")
            return iq

        time.sleep(3)


def esperar_cierre():
    while int(time.time()) % 60 != 59:
        time.sleep(0.05)


def esperar_apertura():
    while int(time.time()) % 60 != 0:
        time.sleep(0.01)


def obtener_pares(iq):
    try:
        activos = iq.get_all_ACTIVES_OPCODE()
        return list(activos.keys())
    except:
        return []


def ejecutar(iq, par, accion):

    status, trade_id = iq.buy(MONTO, par, accion, EXPIRACION)

    if status:
        print(f"ENTRADA: {accion.upper()} {par}")
        send_message(f"🎯 {accion.upper()} {par}")


def run():

    iq = connect()

    while True:

        esperar_cierre()

        pares = obtener_pares(iq)

        for par in pares:

            señal = detectar_entrada(iq, par)

            if señal:

                accion = señal["action"]

                print(f"SEÑAL: {par} {accion}")
                send_message(f"🚨 SEÑAL {par} {accion}")

                esperar_apertura()

                ejecutar(iq, par, accion)

                break


if __name__ == "__main__":
    run()
