import os
import time
from iqoptionapi.stable_api import IQ_Option
from strategy import detectar_trampa
from telegram_bot import send_message

IQ_EMAIL = os.getenv("IQ_EMAIL")
IQ_PASSWORD = os.getenv("IQ_PASSWORD")

PARES = [
    "EURUSD-OTC","GBPUSD-OTC","EURJPY-OTC",
    "USDCHF-OTC","GBPJPY-OTC","AUDUSD-OTC"
]

MONTO = 20000
EXPIRACION = 1


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
            print("🔥 SNIPER ACTIVO")
            send_message("🔥 SNIPER ACTIVO")
            return iq

        time.sleep(3)


def esperar_cierre():
    while int(time.time()) % 60 != 59:
        time.sleep(0.05)
    time.sleep(1.1)  # 🔥 cierre real confirmado


def esperar_apertura():
    while int(time.time()) % 60 != 0:
        time.sleep(0.01)
    time.sleep(0.2)  # 🔥 entrada exacta


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


def run():

    iq = connect()

    while True:

        # 🔥 1. ESPERA CIERRE
        esperar_cierre()

        señal_guardada = None
        par_guardado = None

        # 🔥 2. BUSCA SEÑAL (UNA SOLA VEZ)
        for par in PARES:

            señal = detectar_trampa(iq, par)

            if señal:
                señal_guardada = señal["action"]
                par_guardado = par
                break

        # 🔒 SI NO HAY SEÑAL → CONTINÚA
        if not señal_guardada:
            continue

        send_message(f"🎯 SNIPER DETECTADO {par_guardado} {señal_guardada}")

        # 🔥 3. ESPERA APERTURA (SIN RECALCULAR)
        esperar_apertura()

        # 🔥 4. EJECUTA EXACTO
        ejecutar(iq, par_guardado, señal_guardada)


if __name__ == "__main__":
    run()
