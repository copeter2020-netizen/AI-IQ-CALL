import os
import time
import sys

# 🔥 BLOQUEAR ERRORES IQ OPTION
class NullWriter:
    def write(self, _): pass
    def flush(self): pass

sys.stderr = NullWriter()

from iqoptionapi.stable_api import IQ_Option
from strategy import detectar_entrada
from telegram_bot import send_message

IQ_EMAIL = os.getenv("IQ_EMAIL")
IQ_PASSWORD = os.getenv("IQ_PASSWORD")

MONTO = 2000
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
            print("BOT ACTIVADO")
            send_message("🔥 BOT ACTIVADO")
            return iq

        time.sleep(3)


# 🔥 PARES ACTIVOS
def get_pares(iq):
    pares = []

    all_open = silent(iq.get_all_open_time)

    if not all_open:
        return pares

    try:
        digital = all_open.get("digital", {})

        for par, data in digital.items():
            if data.get("open"):
                pares.append(par)
    except:
        pass

    return pares


# 🔥 ENTRADA ANTES DEL CIERRE (SNIPER REAL)
def esperar_pre_cierre():
    while int(time.time()) % 60 != 58:
        time.sleep(0.01)


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


def ejecutar(iq, par, accion):

    status, trade_id = silent(
        iq.buy, MONTO, par, accion, EXPIRACION
    )

    if status:
        print(f"ENTRADA: {accion.upper()} {par}")
        send_message(f"🎯 {accion.upper()} {par}")
        resultado(iq, trade_id)


def run():

    iq = connect()

    while True:

        pares = get_pares(iq)

        if not pares:
            time.sleep(1)
            continue

        for par in pares:

            señal = detectar_entrada(iq, par)

            if señal:
                print(f"SEÑAL: {par} {señal['action']}")
                send_message(f"🚨 {par} {señal['action']}")

                # 🔥 ENTRADA ANTES DEL CIERRE
                esperar_pre_cierre()

                ejecutar(iq, par, señal["action"])
                break


if __name__ == "__main__":
    run()
