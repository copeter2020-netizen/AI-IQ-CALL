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
# 🔒 SAFE (ANTI ERRORES)
# ==========================
def safe(func, *args, **kwargs):
    try:
        return func(*args, **kwargs)
    except:
        return None


# ==========================
# 🔌 CONEXIÓN
# ==========================
def connect():
    while True:
        iq = IQ_Option(IQ_EMAIL, IQ_PASSWORD)
        safe(iq.connect)

        if iq.check_connect():
            iq.change_balance("PRACTICE")  # 🔥 usa demo (puedes cambiar a REAL)
            print("BOT ACTIVADO")
            send_message("🔥 BOT OPERANDO REAL")
            return iq

        time.sleep(3)


# ==========================
# ⏱️ TIEMPOS SNIPER
# ==========================
def esperar_cierre():
    while int(time.time()) % 60 != 59:
        time.sleep(0.03)


def esperar_apertura():
    while int(time.time()) % 60 != 0:
        time.sleep(0.005)


# ==========================
# 📊 PARES ACTIVOS REALES
# ==========================
def obtener_pares(iq):

    pares_validos = []

    try:
        activos = iq.get_all_ACTIVES_OPCODE()
        open_time = iq.get_all_open_time()
    except:
        return []

    for par in activos.keys():
        try:
            if open_time["digital"][par]["open"]:
                pares_validos.append(par)
        except:
            continue

    return pares_validos


# ==========================
# 💥 EJECUCIÓN REAL
# ==========================
def ejecutar(iq, par, accion):

    try:
        # 🔥 activar digitales
        iq.subscribe_strike_list(par, EXPIRACION)
        time.sleep(1)

        # 🔥 ejecutar operación REAL
        status, trade_id = iq.buy_digital(
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
    else:
        print("FALLO ENTRADA")


# ==========================
# 🚀 LOOP PRINCIPAL
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

            if señal:

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
