import os
import time
from iqoptionapi.stable_api import IQ_Option
from strategy import detectar_trampa
from telegram_bot import send_message, send_image

IQ_EMAIL = os.getenv("IQ_EMAIL")
IQ_PASSWORD = os.getenv("IQ_PASSWORD")

PARES_OTC = [
    "EURUSD-OTC",
    "GBPUSD-OTC",
    "EURJPY-OTC",
    "USDCHF-OTC",
    "GBPJPY-OTC",
    "AUDUSD-OTC",
    "AUDCAD-OTC",
    "AUDJPY-OTC",
    "AUDNZD-OTC",
    "CADCHF-OTC",
    "CADJPY-OTC",
    "CHFJPY-OTC",
    "EURAUD-OTC",
    "EURCAD-OTC",
    "EURCHF-OTC",
    "EURNZD-OTC",
    "GBPAUD-OTC",
    "GBPCAD-OTC",
    "GBPCHF-OTC",
    "GBPNZD-OTC",
    "NZDUSD-OTC",
    "NZDJPY-OTC",
    "NZDCAD-OTC",
    "NZDCHF-OTC",
    "USDCAD-OTC",
    "USDJPY-OTC",
    "USDNOK-OTC",
    "USDSEK-OTC",
    "USDTRY-OTC",
    "USDZAR-OTC",
    "USDSGD-OTC",
    "USDHKD-OTC",
    "USDTHB-OTC",
    "USDMXN-OTC",
    "USDINR-OTC",
    "USDIDR-OTC",
    "USDARS-OTC",
    "USDCLP-OTC",
    "USDCOP-OTC",
    "USDNGN-OTC",
    "USDVND-OTC",
    "USDPLN-OTC",
    "USDPKR-OTC",
    "USDHUF-OTC",
    "USDCZK-OTC",
    "USDILS-OTC",
    "USDQAR-OTC",
    "USDKZT-OTC",
    "USDBDT-OTC",
    "USDGHS-OTC"
]

MONTO = 12000
EXPIRACION = 1

BOT_ACTIVO = True


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
            send_message("🔥 SNIPER ACTIVO CON LISTA OTC COMPLETA")
            return iq

        time.sleep(3)


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

    # 🔥 ENTRADAS INVERTIDAS
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

        if not BOT_ACTIVO:
            time.sleep(1)
            continue

        esperar_cierre()

        señal_guardada = None
        par_guardado = None

        # 🔥 ANALIZA TODOS LOS PARES OTC
        for par in PARES_OTC:

            señal = detectar_trampa(iq, par)

            if señal:
                señal_guardada = señal["action"]
                par_guardado = par
                break

        if not señal_guardada:
            continue

        send_message(f"🚨 SEÑAL {par_guardado} {señal_guardada}")

        esperar_apertura()

        ejecutar(iq, par_guardado, señal_guardada)


if __name__ == "__main__":
    run()
