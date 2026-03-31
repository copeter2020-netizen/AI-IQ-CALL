import os
import time
from iqoptionapi.stable_api import IQ_Option
from strategy import detectar_trampa
from telegram_bot import send_message

IQ_EMAIL = os.getenv("IQ_EMAIL")
IQ_PASSWORD = os.getenv("IQ_PASSWORD")

# 🔥 TODOS TUS PARES (SNIPER)
PARES = [
    "EURUSD-OTC","GBPUSD-OTC","EURJPY-OTC","USDCHF-OTC",
    "GBPJPY-OTC","AUDUSD-OTC","EURGBP-OTC","USDHKD-OTC",
    "AUDCAD-OTC","GBPCAD-OTC"
]

MONTO = 20000
EXPIRACION = 1

CONTROL_FILE = "estado.txt"


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
            print("🔥 BOT SNIPER ACTIVO")
            send_message("🔥 BOT SNIPER ACTIVO")
            return iq

        time.sleep(3)


def esperar_cierre_real():
    while True:
        if int(time.time()) % 60 == 59:
            time.sleep(1.2)
            return
        time.sleep(0.1)


def esperar_apertura_real():
    while True:
        if int(time.time()) % 60 == 0:
            time.sleep(0.3)
            return
        time.sleep(0.05)


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

    status, trade_id = silent(
        iq.buy, MONTO, par, accion, EXPIRACION
    )

    if status:
        send_message(f"🎯 {accion.upper()} {par}")
        resultado(iq, trade_id)
    else:
        send_message(f"⛔ Error en {par}")


def run():

    iq = connect()

    while True:

        esperar_cierre_real()

        señal_encontrada = False

        # 🔥 ESCANEO SNIPER (NO PIERDE ENTRADAS)
        for par in PARES:

            señal = detectar_trampa(iq, par)

            if señal:

                accion = señal["action"]

                send_message(f"🎯 SNIPER {par} {accion}")

                esperar_apertura_real()

                ejecutar(iq, par, accion)

                señal_encontrada = True
                break

        # 🔥 SI NO HAY SEÑAL → SIGUE BUSCANDO
        if not señal_encontrada:
            continue


if __name__ == "__main__":
    run()
