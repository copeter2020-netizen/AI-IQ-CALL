import os
import time
import sys
import logging

# ==========================
# 🔥 BLOQUEO TOTAL CONSOLA
# ==========================
class CleanConsole:
    def write(self, msg):
        if any(x in msg for x in ["BOT ACTIVADO", "SEÑAL:", "ENTRADA:", "WIN", "LOSS"]):
            sys.__stdout__.write(msg)

    def flush(self):
        pass


sys.stdout = CleanConsole()
sys.stderr = CleanConsole()
logging.getLogger().setLevel(logging.CRITICAL)

# ==========================
# IMPORTS
# ==========================
from iqoptionapi.stable_api import IQ_Option
from strategy import detectar_trampa
from telegram_bot import send_message

IQ_EMAIL = os.getenv("IQ_EMAIL")
IQ_PASSWORD = os.getenv("IQ_PASSWORD")

MONTO = 20000
EXPIRACION = 1


# ==========================
# 🔒 SILENCIADOR
# ==========================
def silent(func, *args, **kwargs):
    try:
        return func(*args, **kwargs)
    except:
        return None


# ==========================
# 🔥 CONEXIÓN
# ==========================
def connect():
    while True:
        iq = IQ_Option(IQ_EMAIL, IQ_PASSWORD)
        silent(iq.connect)

        if iq.check_connect():
            print("BOT ACTIVADO")
            send_message("🔥 BOT ACTIVADO")
            return iq

        time.sleep(3)


# ==========================
# 🔥 PARES ACTIVOS
# ==========================
def get_pares_activos(iq):
    try:
        open_time = iq.get_all_open_time()
    except:
        return []

    pares = []

    try:
        for par, data in open_time["binary"].items():
            if "-OTC" in par and data["open"]:
                pares.append(par)
    except:
        return []

    return pares


# ==========================
# 🔥 RESULTADO
# ==========================
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

        if r > 0:
            print("WIN")
            send_message("✅ WIN")
        else:
            print("LOSS")
            send_message("❌ LOSS")

        return


# ==========================
# 🚀 EJECUCIÓN INMEDIATA
# ==========================
def ejecutar(iq, par, accion):

    # 🔥 INVERTIDO
    accion = "put" if accion == "call" else "call"

    print(f"ENTRADA: {accion.upper()} {par}")
    send_message(f"🎯 {accion.upper()} {par}")

    status, trade_id = silent(
        iq.buy, MONTO, par, accion, EXPIRACION
    )

    if status:
        resultado(iq, trade_id)


# ==========================
# 🔥 MAIN
# ==========================
def run():

    iq = connect()

    while True:

        pares = get_pares_activos(iq)

        if not pares:
            time.sleep(1)
            continue

        for par in pares:

            señal = None

            try:
                señal = detectar_trampa(iq, par)
            except:
                continue

            if señal:
                print(f"SEÑAL: {par} {señal['action']}")
                send_message(f"🚨 SEÑAL {par} {señal['action']}")

                # 🔥 ENTRA INMEDIATO (SIN ESPERAR)
                ejecutar(iq, par, señal["action"])
                break


if __name__ == "__main__":
    run()
