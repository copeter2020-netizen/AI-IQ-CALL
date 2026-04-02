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
# 🔥 OBTENER PARES OTC ACTIVOS
# ==========================
def obtener_pares_otc(iq):

    activos = iq.get_all_open_time()

    pares = []

    try:
        for par, data in activos["binary"].items():

            if "OTC" in par and data["open"]:
                pares.append(par)

    except:
        pass

    return pares


# ==========================
# 🔥 CONEXIÓN
# ==========================
def connect():
    while True:
        iq = IQ_Option(IQ_EMAIL, IQ_PASSWORD)
        silent(iq.connect)

        if iq.check_connect():
            send_message("🔥 BOT AUTO OTC ACTIVO")
            return iq

        time.sleep(3)


# ==========================
def esperar_cierre():
    while int(time.time()) % 60 != 59:
        time.sleep(0.05)
    time.sleep(1)


def esperar_apertura():
    while int(time.time()) % 60 != 0:
        time.sleep(0.01)
    time.sleep(0.2)


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
# 🔥 EJECUCIÓN
# ==========================
def ejecutar(iq, par, accion):

    status, trade_id = silent(
        iq.buy, MONTO, par, accion, EXPIRACION
    )

    if status:
        send_message(f"🎯 {accion.upper()} {par}")
        resultado(iq, trade_id)


# ==========================
# 🔥 BOT PRINCIPAL
# ==========================
def run():

    iq = connect()

    while True:

        esperar_cierre()

        pares = obtener_pares_otc(iq)

        if not pares:
            send_message("⚠️ No hay pares OTC activos")
            time.sleep(5)
            continue

        señal = None
        par_elegido = None

        # 🔥 ANALIZA TODOS LOS DISPONIBLES
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
