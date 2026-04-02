import os
import time
from iqoptionapi.stable_api import IQ_Option
from strategy import detectar_trampa
from telegram_bot import send_message, send_image

IQ_EMAIL = os.getenv("IQ_EMAIL")
IQ_PASSWORD = os.getenv("IQ_PASSWORD")

MONTO = 12000
EXPIRACION = 1
PAYOUT_MINIMO = 80


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
            print("🔥 BOT ACTIVO")
            send_message("🔥 BOT ACTIVO")
            return iq

        time.sleep(3)


# 🔥 SOLO ACTIVOS REALES (FIX ERROR)
def obtener_pares_validos(iq):

    try:
        open_time = iq.get_all_open_time()
        profit = iq.get_all_profit()
    except:
        return []

    pares = []

    for tipo in ["binary", "turbo"]:

        if tipo not in open_time:
            continue

        for par, data in open_time[tipo].items():

            if not data.get("open"):
                continue

            if "-OTC" not in par:
                continue

            try:
                payout = int(profit[par]["turbo"] * 100)
            except:
                continue

            if payout < PAYOUT_MINIMO:
                continue

            pares.append(par)

    return list(set(pares))


def esperar_cierre():
    while int(time.time()) % 60 != 59:
        time.sleep(0.05)
    time.sleep(1.1)


def esperar_apertura():
    while int(time.time()) % 60 != 0:
        time.sleep(0.01)
    time.sleep(0.2)


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
            send_image("https://i.imgur.com/2QZ7Z6G.png", "WIN 🟢")
        else:
            print("LOSS")
            send_message("❌ LOSS")
            send_image("https://i.imgur.com/Z6X7XwL.png", "LOSS 🔴")

        return


def ejecutar(iq, par, accion):

    if accion == "call":
        accion = "put"
    else:
        accion = "call"

    print(f"ENTRADA: {accion.upper()} {par}")
    send_message(f"🚨 ENTRADA {accion.upper()} {par}")

    status, trade_id = silent(
        iq.buy, MONTO, par, accion, EXPIRACION
    )

    if status:
        resultado(iq, trade_id)


def run():

    iq = connect()

    while True:

        esperar_cierre()

        pares = obtener_pares_validos(iq)

        if not pares:
            print("Sin pares válidos")
            time.sleep(2)
            continue

        for par in pares:

            try:
                señal = detectar_trampa(iq, par)
            except:
                continue

            if señal:
                print(f"SEÑAL DETECTADA: {par} {señal['action']}")
                send_message(f"🎯 SEÑAL {par} {señal['action']}")

                esperar_apertura()
                ejecutar(iq, par, señal["action"])
                break


if __name__ == "__main__":
    run()
