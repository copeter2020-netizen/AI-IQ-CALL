import os
import time
from iqoptionapi.stable_api import IQ_Option
from strategy import detectar_trampa
from telegram_bot import send_message

IQ_EMAIL = os.getenv("IQ_EMAIL")
IQ_PASSWORD = os.getenv("IQ_PASSWORD")

PARES = [
    "EURUSD-OTC","GBPUSD-OTC","EURJPY-OTC",
    "USDCHF-OTC","GBPJPY-OTC","AUDUSD-OTC"
]

MONTO = 20000
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
            print("🔥 SNIPER ACTIVO")
            send_message("🔥 SNIPER ACTIVO")
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


# 🔥 RESULTADO MEJORADO
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

        # 🔥 MENSAJE CLARO
        if r > 0:
            mensaje = f"✅ WIN +{round(r,2)}"
        elif r < 0:
            mensaje = f"❌ LOSS {round(r,2)}"
        else:
            mensaje = "⚖️ EMPATE"

        print(mensaje)
        send_message(mensaje)

        return


def ejecutar(iq, par, accion):

    status, trade_id = silent(
        iq.buy, MONTO, par, accion, EXPIRACION
    )

    if status:
        send_message(f"🎯 {accion.upper()} {par}")
        resultado(iq, trade_id)
    else:
        send_message(f"⛔ ERROR EN {par}")


def run():

    iq = connect()

    while True:

        esperar_cierre()

        señal_guardada = None
        par_guardado = None

        for par in PARES:

            señal = detectar_trampa(iq, par)

            if señal:
                señal_guardada = señal["action"]
                par_guardado = par
                break

        if not señal_guardada:
            continue

        send_message(f"🎯 SNIPER DETECTADO {par_guardado} {señal_guardada}")

        esperar_apertura()

        ejecutar(iq, par_guardado, señal_guardada)


if __name__ == "__main__":
    run()
