import os
import time
from iqoptionapi.stable_api import IQ_Option
from strategy import detectar_trampa
from telegram_bot import send_message

IQ_EMAIL = os.getenv("IQ_EMAIL")
IQ_PASSWORD = os.getenv("IQ_PASSWORD")

MONTO = 20000
EXPIRACION = 1

BOT_ACTIVO = True


# ==========================
# 🔇 BLOQUEADOR TOTAL ERRORES
# ==========================
def silent(func, *args, **kwargs):
    try:
        return func(*args, **kwargs)
    except:
        return None


# ==========================
# 🔌 CONEXIÓN
# ==========================
def connect():
    while True:
        iq = IQ_Option(IQ_EMAIL, IQ_PASSWORD)
        silent(iq.connect)

        if iq.check_connect():
            print("BOT ACTIVADO")
            send_message("🔥 BOT ACTIVADO")
            return iq

        time.sleep(3)


# ==========================
# ⏱️ SNIPER (APERTURA EXACTA)
# ==========================
def esperar_cierre():
    while int(time.time()) % 60 != 59:
        time.sleep(0.01)
    time.sleep(0.8)


def esperar_apertura():
    while int(time.time()) % 60 != 0:
        time.sleep(0.001)


# ==========================
# 📊 RESULTADO
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
# 🚀 EJECUTAR OPERACIÓN
# ==========================
def ejecutar(iq, par, accion):

    # 🔥 INVERTIDO (como tú lo quieres)
    if accion == "call":
        accion = "put"
    else:
        accion = "call"

    status, trade_id = silent(
        iq.buy, MONTO, par, accion, EXPIRACION
    )

    if status:
        print(f"ENTRADA: {accion.upper()} {par}")
        send_message(f"🎯 ENTRADA: {accion.upper()} {par}")
        resultado(iq, trade_id)


# ==========================
# 🔥 OBTENER SOLO PARES ACTIVOS
# ==========================
def get_activos(iq):
    activos = []

    all_open = silent(iq.get_all_open_time)

    if not all_open:
        return activos

    try:
        for par, data in all_open["digital"].items():
            if data["open"]:
                activos.append(par)
    except:
        pass

    return activos


# ==========================
# 🧠 LOOP PRINCIPAL
# ==========================
def run():

    iq = connect()

    while True:

        if not BOT_ACTIVO:
            time.sleep(1)
            continue

        esperar_cierre()

        pares = get_activos(iq)

        if not pares:
            continue

        señal = None
        par_elegido = None

        # 🔥 ANALIZA SOLO PARES ACTIVOS
        for par in pares:

            data = detectar_trampa(iq, par)

            if data:
                señal = data["action"]
                par_elegido = par
                break

        if not señal:
            continue

        print(f"SEÑAL: {par_elegido} {señal}")
        send_message(f"🚨 SEÑAL: {par_elegido} {señal}")

        esperar_apertura()

        ejecutar(iq, par_elegido, señal)


# ==========================
# ▶️ START
# ==========================
if __name__ == "__main__":
    run()
