import os
import time
from iqoptionapi.stable_api import IQ_Option
from strategy import detectar_trampa
from telegram_bot import send_message, send_image_url

IQ_EMAIL = os.getenv("IQ_EMAIL")
IQ_PASSWORD = os.getenv("IQ_PASSWORD")

MONTO = 20000
EXPIRACION = 1


def silent(func, *args, **kwargs):
    try:
        return func(*args, **kwargs)
    except:
        return None


# ==========================
# 🔥 PARES BINARIOS REALES
# ==========================
def obtener_pares_binarios(iq):

    pares_validos = []

    try:
        activos = iq.get_all_open_time()
        profit = iq.get_all_profit()

        for par, data in activos["binary"].items():

            if not data["open"]:
                continue

            # 🔥 SOLO OTC FOREX REALES
            if "OTC" not in par:
                continue

            # 🔒 FILTRO PARA EVITAR CRYPTO/STOCKS
            if "/" in par:
                continue

            # 🔥 VALIDAR QUE EXISTA PROFIT
            if par not in profit:
                continue

            pares_validos.append(par)

    except:
        pass

    return pares_validos


# ==========================
def connect():
    while True:
        iq = IQ_Option(IQ_EMAIL, IQ_PASSWORD)
        silent(iq.connect)

        if iq.check_connect():
            send_message("🔥 BOT BINARIAS REALES ACTIVO")
            return iq

        time.sleep(3)


def esperar_cierre():
    while int(time.time()) % 60 != 59:
        time.sleep(0.05)
    time.sleep(1)


def esperar_apertura():
    while int(time.time()) % 60 != 0:
        time.sleep(0.01)
    time.sleep(0.2)


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
            send_image_url(
                "https://i.imgur.com/2QZ7Z6G.png",
                f"✅ WIN +{r}"
            )
        else:
            send_image_url(
                "https://i.imgur.com/Z6X7XwL.png",
                f"❌ LOSS {r}"
            )

        return


# ==========================
def ejecutar(iq, par, accion):

    status, trade_id = silent(
        iq.buy, MONTO, par, accion, EXPIRACION
    )

    if status:
        send_message(f"🎯 {accion.upper()} {par}")
        resultado(iq, trade_id)


# ==========================
def run():

    iq = connect()

    while True:

        esperar_cierre()

        pares = obtener_pares_binarios(iq)

        if not pares:
            send_message("⚠️ No hay pares binarios disponibles")
            time.sleep(5)
            continue

        señal = None
        par_elegido = None

        # 🔥 ANALIZA SOLO PARES REALES
        for par in pares:

            señal_data = detectar_trampa(iq, par)

            if señal_data:
                señal = señal_data["action"]
                par_elegido = par
                break

        if not señal:
            continue

        send_message(f"🚨 TRAMPA DETECTADA {par_elegido} {señal}")

        esperar_apertura()

        ejecutar(iq, par_elegido, señal)


if __name__ == "__main__":
    run()
