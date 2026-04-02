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
# 🔒 BLOQUEADOR TOTAL DE ERRORES
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
            iq.change_balance("PRACTICE")
            print("BOT ACTIVADO")
            send_message("🔥 BOT ACTIVO SIN ERRORES")
            return iq

        time.sleep(3)


# ==========================
# ⏱️ TIEMPO EXACTO
# ==========================
def esperar_cierre():
    while int(time.time()) % 60 != 59:
        time.sleep(0.02)


def esperar_apertura():
    while int(time.time()) % 60 != 0:
        time.sleep(0.002)


# ==========================
# 📊 PARES ACTIVOS REALES
# ==========================
def obtener_pares(iq):

    pares = []

    try:
        open_time = iq.get_all_open_time()
    except:
        return []

    for par in open_time.get("digital", {}):
        try:
            if open_time["digital"][par]["open"]:
                pares.append(par)
        except:
            continue

    return pares


# ==========================
# 🚫 ANTI ERROR UNDERLYING
# ==========================
def preparar_par(iq, par):

    try:
        iq.subscribe_strike_list(par, EXPIRACION)
        time.sleep(1.5)

        data = iq.get_digital_underlying_list_data()
        if not data:
            return False

        return True

    except:
        return False


# ==========================
# 💥 EJECUCIÓN SEGURA REAL
# ==========================
def ejecutar(iq, par, accion):

    # 🔥 evitar error underlying
    if not preparar_par(iq, par):
        return

    try:
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
