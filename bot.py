import os
import time
from iqoptionapi.stable_api import IQ_Option
from strategy import detectar_trampa
from telegram_bot import send_message, send_image_url

IQ_EMAIL = os.getenv("IQ_EMAIL")
IQ_PASSWORD = os.getenv("IQ_PASSWORD")

PARES_OTC = [
    "EURUSD-OTC","GBPUSD-OTC","EURJPY-OTC","USDCHF-OTC",
    "GBPJPY-OTC","AUDUSD-OTC","AUDCAD-OTC","AUDJPY-OTC",
    "AUDNZD-OTC","CADCHF-OTC","CADJPY-OTC","CHFJPY-OTC",
    "EURAUD-OTC","EURCAD-OTC","EURCHF-OTC","EURNZD-OTC",
    "GBPAUD-OTC","GBPCAD-OTC","GBPCHF-OTC","GBPNZD-OTC",
    "NZDUSD-OTC","NZDJPY-OTC","NZDCAD-OTC","NZDCHF-OTC",
    "USDCAD-OTC","USDJPY-OTC","USDZAR-OTC","USDSGD-OTC",
    "USDHKD-OTC"
]

MONTO = 2000
EXPIRACION = 1  # 🔥 1 MINUTOS


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
            send_message("🔥 BOT 2M ACTIVADO")
            return iq

        time.sleep(3)


def esperar_cierre():
    while int(time.time()) % 60 != 59:
        time.sleep(0.05)
    time.sleep(1.2)


def esperar_apertura():
    while int(time.time()) % 60 != 0:
        time.sleep(0.01)
    time.sleep(0.3)


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
            send_image_url("https://i.imgur.com/2QZ7Z6G.png", f"✅ WIN +{r}")
        else:
            send_image_url("https://i.imgur.com/Z6X7XwL.png", f"❌ LOSS {r}")

        return


def ejecutar(iq, par, accion):
    status, trade_id = silent(
        iq.buy, MONTO, par, accion, EXPIRACION
    )

    if status:
        send_message(f"🎯 {accion.upper()} {par} (2M)")
        resultado(iq, trade_id)


def run():

    iq = connect()

    while True:

        esperar_cierre()

        señal = None
        par = None

        for p in PARES_OTC:

            s = detectar_trampa(iq, p)

            if s:
                señal = s["action"]
                par = p
                break

        if not señal:
            continue

        send_message(f"🚨 CONFIRMADA {par} {señal}")

        esperar_apertura()

        ejecutar(iq, par, señal)


if __name__ == "__main__":
    run()
