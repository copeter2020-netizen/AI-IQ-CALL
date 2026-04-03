import os
import time
from iqoptionapi.stable_api import IQ_Option
from strategy import detectar_entrada
from telegram_bot import send_message

IQ_EMAIL = os.getenv("IQ_EMAIL")
IQ_PASSWORD = os.getenv("IQ_PASSWORD")

MONTO = 2000
EXPIRACION = 1

PAR = "EURUSD"   # 🔥 SOLO ESTE PAR


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
            send_message("🔥 BOT SNIPER ACTIVO EURUSD")
            return iq

        time.sleep(3)


# ==========================
# ⏱️ ESPERAR APERTURA VELA
# ==========================
def esperar_apertura():
    while int(time.time()) % 60 != 0:
        time.sleep(0.001)


# ==========================
# 💥 EJECUCIÓN
# ==========================
def ejecutar(iq, accion):

    try:
        status, _ = iq.buy(
            MONTO,
            PAR,
            accion,
            EXPIRACION
        )
    except:
        return

    if status:
        print(f"ENTRADA: {accion.upper()} {PAR}")
        send_message(f"🎯 {PAR} {accion.upper()}")


# ==========================
# 🚀 LOOP PRINCIPAL
# ==========================
def run():

    iq = connect()

    while True:

        # 🔥 ANALIZA CADA SEGUNDO
        señal = detectar_entrada(iq, PAR)

        if señal:

            accion = señal["action"]

            print(f"SEÑAL DETECTADA: {accion}")

            # ⏱️ ESPERA CIERRE EXACTO
            esperar_apertura()

            ejecutar(iq, accion)

        time.sleep(1)  # 🔥 análisis cada segundo


# ==========================
# ▶️ START
# ==========================
if __name__ == "__main__":
    run()
