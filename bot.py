import os
import time
from iqoptionapi.stable_api import IQ_Option
from strategy import detectar_trampa
from telegram_bot import send_message, send_image

IQ_EMAIL = os.getenv("IQ_EMAIL")
IQ_PASSWORD = os.getenv("IQ_PASSWORD")

MONTO = 20000
EXPIRACION = 1

PAYOUT_MINIMO = 80  # 🔥 filtro PRO


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
            send_message("🔥 BOT PRO MAX ACTIVO (OTC + FILTRO)")
            return iq

        time.sleep(3)


# ==========================
# 🔥 FILTRO PRO MAX
# ==========================
def obtener_pares_pro(iq):

    abiertos = iq.get_all_open_time()
    profit = iq.get_all_profit()

    pares = []

    for tipo in ["turbo", "binary"]:
        for par, data in abiertos[tipo].items():

            if not data["open"]:
                continue

            if "-OTC" not in par:
                continue

            payout = 0

            try:
                payout = int(profit[par]["turbo"] * 100)
            except:
                continue

            if payout >= PAYOUT_MINIMO:
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
            send_message("✅ WIN")
            send_image("https://i.imgur.com/2QZ7Z6G.png", "WIN 🟢")
        else:
            send_message("❌ LOSS")
            send_image("https://i.imgur.com/Z6X7XwL.png", "LOSS 🔴")

        return


def ejecutar(iq, par, accion):

    # 😈 ENTRADAS INVERTIDAS
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
            send_message("⚠️ No hay pares válidos")
            time.sleep(5)
            continue

        señal_guardada = None
        par_guardado = None

        for par in pares:

            señal = detectar_trampa(iq, par)

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
