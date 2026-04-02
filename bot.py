import os
import time
import sys
import logging

# ==========================
# 🔥 BLOQUEO TOTAL DE ERRORES
# ==========================
class DevNull:
    def write(self, msg):
        if any(x in msg.lower() for x in [
            "asset", "not found", "underlying", "error"
        ]):
            return
        sys.__stdout__.write(msg)

    def flush(self):
        pass


sys.stdout = DevNull()
sys.stderr = DevNull()

logging.getLogger().setLevel(logging.CRITICAL)

# ==========================
# IMPORTS
# ==========================
from iqoptionapi.stable_api import IQ_Option
from strategy import detectar_trampa
from telegram_bot import send_message

IQ_EMAIL = os.getenv("IQ_EMAIL")
IQ_PASSWORD = os.getenv("IQ_PASSWORD")

MONTO = 7900
EXPIRACION = 1


# ==========================
# 🔥 FUNCIONES SEGURAS
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
            print("🔥 BOT SNIPER ACTIVO")
            send_message("🔥 BOT SNIPER ACTIVO")
            return iq

        time.sleep(3)


# ==========================
# 🔥 PARES REALES (SIN FALLAR)
# ==========================
def get_pares_activos(iq):

    try:
        open_time = iq.get_all_open_time()
    except:
        return []

    pares = []

    try:
        for par, data in open_time["binary"].items():

            if not isinstance(par, str):
                continue

            if "-OTC" not in par:
                continue

            if not data.get("open"):
                continue

            # 🔥 FILTRO EXTRA (evita underlying error)
            if "/" in par or " " in par:
                continue

            pares.append(par)

    except:
        return []

    return pares


# ==========================
# 🔥 TIMING SNIPER
# ==========================
def esperar_cierre():
    while int(time.time()) % 60 != 59:
        time.sleep(0.005)


def esperar_apertura():
    while int(time.time()) % 60 != 0:
        pass  # 🔥 SIN DELAY


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
# 🔥 EJECUCIÓN
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

        esperar_cierre()

        for par in pares:

            señal = None

            try:
                señal = detectar_trampa(iq, par)
            except:
                continue

            if señal:
                print(f"SEÑAL: {par} {señal['action']}")
                send_message(f"🚨 SEÑAL {par} {señal['action']}")

                esperar_apertura()
                ejecutar(iq, par, señal["action"])
                break


if __name__ == "__main__":
    run() 
