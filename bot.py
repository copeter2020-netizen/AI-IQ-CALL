import os
import time
from iqoptionapi.stable_api import IQ_Option
from strategy import detectar_entrada

IQ_EMAIL = os.getenv("IQ_EMAIL")
IQ_PASSWORD = os.getenv("IQ_PASSWORD")

PAR = "EURUSD"
MONTO = 20000
EXPIRACION = 1


def connect():
    while True:
        iq = IQ_Option(IQ_EMAIL, IQ_PASSWORD)
        iq.connect()

        if iq.check_connect():
            iq.change_balance("PRACTICE")
            print("BOT ACTIVADO")
            return iq

        time.sleep(3)


def esperar_sniper():
    while int(time.time()) % 60 != 59:
        time.sleep(0.001)


def ejecutar(iq, accion):
    try:
        status, _ = iq.buy(MONTO, PAR, accion, EXPIRACION)
    except:
        return

    if status:
        print(f"ENTRADA REAL: {accion.upper()}")


def run():

    iq = connect()

    while True:

        señal = detectar_entrada(iq, PAR)

        if señal:
            print(f"SEÑAL DETECTADA: {señal}")

            esperar_sniper()
            ejecutar(iq, señal)

        time.sleep(1)


if __name__ == "__main__":
    run()
