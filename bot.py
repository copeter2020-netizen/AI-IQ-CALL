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
            send_message("🔥 BOT ACTIVO PRICE ACTION")
            return iq

        time.sleep(3)


def esperar_cierre():
    while int(time.time()) % 60 != 59:
        time.sleep(0.05)


def esperar_apertura():
    while int(time.time()) % 60 != 0:
        time.sleep(0.01)


def obtener_pares(iq):
    activos = safe(iq.get_all_ACTIVES_OPCODE)

    if not activos:
        return []

    return list(activos.keys())


def ejecutar(iq, par, accion):

    result = safe(iq.buy, MONTO, par, accion, EXPIRACION)

    if not result:
        return

    status, trade_id = result

    if status:
        print(f"ENTRADA: {accion.upper()} {par}")
        send_message(f"🎯 {accion.upper()} {par}")


def run():

    iq = connect()

    while True:

        esperar_cierre()

        pares = obtener_pares(iq)

        if not pares:
            continue

        señal_encontrada = False

        for par in pares:

            señal = detectar_entrada(iq, par)

            if señal:

                accion = señal["action"]

                print(f"SEÑAL: {par} {accion}")
                send_message(f"🚨 SEÑAL {par} {accion}")

                esperar_apertura()

                ejecutar(iq, par, accion)

                señal_encontrada = True
                break

        # 🔥 si no encuentra señal sigue buscando sin parar
        if not señal_encontrada:
            continue


if __name__ == "__main__":
    run() 
