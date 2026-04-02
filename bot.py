import os
import time
import sys

# 🔥 BLOQUEAR ERRORES INTERNOS (IQ OPTION)
class NullWriter:
    def write(self, _): pass
    def flush(self): pass

sys.stderr = NullWriter()

from iqoptionapi.stable_api import IQ_Option
from strategy import detectar_trampa, registrar_resultado
from telegram_bot import send_message

IQ_EMAIL = os.getenv("IQ_EMAIL")
IQ_PASSWORD = os.getenv("IQ_PASSWORD")

MONTO = 5000
EXPIRACION = 1

BOT_ACTIVO = True


# ==========================
# 🔇 SILENCIAR FUNCIONES
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
# ⏱️ SNIPER
# ==========================
def esperar_cierre():
    while int(time.time()) % 60 != 59:
        time.sleep(0.01)
    time.sleep(0.8)


def esperar_apertura():
    while int(time.time()) % 60 != 0:
        time.sleep(0.001)


# ==========================
# 📊 RESULTADO + IA
# ==========================
def resultado(iq, trade_id, par):
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
            registrar_resultado(par, "win")
        else:
            print("LOSS")
            send_message("❌ LOSS")
            registrar_resultado(par, "loss")

        return


# ==========================
# 🚀 EJECUTAR
# ==========================
def ejecutar(iq, par, accion):

    # 🔥 ENTRADAS INVERTIDAS
    accion = "put" if accion == "call" else "call"

    status, trade_id = silent(
        iq.buy, MONTO, par, accion, EXPIRACION
    )

    if status:
        print(f"ENTRADA: {accion.upper()} {par}")
        send_message(f"🎯 ENTRADA: {accion.upper()} {par}")
        resultado(iq, trade_id, par)


# ==========================
# 🔥 SOLO ACTIVOS REALES
# ==========================
def get_activos(iq):
    activos = []

    all_open = silent(iq.get_all_open_time)

    if not all_open:
        return activos

    try:
        digital = all_open.get("digital", {})
        for par, data in digital.items():
            if data.get("open"):
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

        # 🔥 ANALIZA SOLO PARES ACTIVOS + IA
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
