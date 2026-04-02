import os
import time
from iqoptionapi.stable_api import IQ_Option
from strategy import detectar_trampa
from telegram_bot import send_message, send_image

IQ_EMAIL = os.getenv("IQ_EMAIL")
IQ_PASSWORD = os.getenv("IQ_PASSWORD")

MONTO = 20000
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
            send_message("🔥 BOT PRO MAX ACTIVO (FIX TOTAL)")
            return iq

        time.sleep(3)


# ==========================
# 🔥 FILTRO REAL SIN ERRORES
# ==========================
def obtener_pares_pro(iq):

    try:
        open_time = iq.get_all_open_time()
        profit = iq.get_all_profit()
    except:
        return []

    pares_validos = []

    for tipo in ["binary", "turbo"]:

        if tipo not in open_time:
            continue

        for par, data in open_time[tipo].items():

            # 🔥 SOLO ABIERTOS
            if not data.get("open"):
                continue

            # 🔥 SOLO OTC
            if "-OTC" not in par:
                continue

            # 🔥 EVITA ACTIVOS FAKE / BUG
            if "/" in par or " " in par:
                continue

            # 🔥 FILTRO PAYOUT
            try:
                payout = int(profit[par]["turbo"] * 100)
            except:
                continue

            if payout < PAYOUT_MINIMO:
                continue

            pares_validos.append(par)

    return list(set(pares_validos))


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
            send_message("✅ WIN")
            send_image("https://i.imgur.com/2QZ7Z6G.png", "WIN 🟢")
        else:
            send_message("❌ LOSS")
            send_image("https://i.imgur.com/Z6X7XwL.png", "LOSS 🔴")

        return


def ejecutar(iq, par, accion):

    # 😈 ENTRADA INVERTIDA
    if accion == "call":
        accion = "put"
    else:
        accion = "call"

    status, trade_id = silent(
        iq.buy, MONTO, par, accion, EXPIRACION
    )

    if status:
        send_message(f"🎯 {accion.upper()} {par}")
        resultado(iq, trade_id)


def run():

    iq = connect()

    while True:

        esperar_cierre()

        pares = obtener_pares_pro(iq)

        if not pares:
            time.sleep(3)
            continue

        señal_guardada = None
        par_guardado = None

        for par in pares:

            try:
                señal = detectar_trampa(iq, par)
            except:
                continue

            if señal:
                señal_guardada = señal["action"]
                par_guardado = par
                break

        if not señal_guardada:
            continue

        send_message(f"🚨 SEÑAL PRO {par_guardado} {señal_guardada}")

        esperar_apertura()

        ejecutar(iq, par_guardado, señal_guardada)


if __name__ == "__main__":
    run()
