import os
import time
from iqoptionapi.stable_api import IQ_Option
from strategy import detectar_entrada
from telegram_bot import send_message

IQ_EMAIL = os.getenv("IQ_EMAIL")
IQ_PASSWORD = os.getenv("IQ_PASSWORD")

MONTO = 2000
EXPIRACION = 1


# ==========================
# 🔌 CONEXIÓN
# ==========================
def connect():
    while True:
        iq = IQ_Option(IQ_EMAIL, IQ_PASSWORD)
        iq.connect()

        if iq.check_connect():
            iq.change_balance("PRACTICE")
            print("BOT ACTIVADO")
            send_message("🔥 BOT ACTIVO SIN ERRORES")
            return iq

        time.sleep(3)


# ==========================
# ⏱️ TIEMPO
# ==========================
def esperar_cierre():
    while int(time.time()) % 60 != 59:
        time.sleep(0.02)


def esperar_apertura():
    while int(time.time()) % 60 != 0:
        time.sleep(0.002)


# ==========================
# 📊 PARES ACTIVOS
# ==========================
def obtener_pares(iq):

    pares = []

    open_time = iq.get_all_open_time()

    for par in open_time.get("binary", {}):
        try:
            if open_time["binary"][par]["open"]:
                pares.append(par)
        except:
            continue

    return pares


# ==========================
# 💥 EJECUCIÓN (SIN ERRORES)
# ==========================
def ejecutar(iq, par, accion):

    try:
        status, trade_id = iq.buy(
            MONTO,
            par,
            accion,
            EXPIRACION
        )
    except:
        return

    if status:
        print(f"ENTRADA: {accion.upper()} {par}")
        send_message(f"🎯 ENTRADA {accion.upper()} {par}")


# ==========================
# 🚀 LOOP
# ==========================
def run():

    iq = connect()

    while True:

        esperar_cierre()

        pares = obtener_pares(iq)

        if not pares:
            continue

        for par in pares:

            señal = detectar_entrada(iq, par)

            if not señal:
                continue

            accion = señal["action"]

            print(f"SEÑAL: {par} {accion}")
            send_message(f"🚨 SEÑAL {par} {accion}")

            esperar_apertura()

            ejecutar(iq, par, accion)

            break


# ==========================
# ▶️ START
# ==========================
if __name__ == "__main__":
    run()
