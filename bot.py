import os
import time
from iqoptionapi.stable_api import IQ_Option
from strategy import detectar_trampa
from telegram_bot import send_message


IQ_EMAIL = os.getenv("IQ_EMAIL")
IQ_PASSWORD = os.getenv("IQ_PASSWORD")

MONTO = 12000
EXPIRACION = 1


def silent(func, *args, **kwargs):
    try:
        return func(*args, **kwargs)
    except:
        return None


# 🔥 FIX TOTAL (ELIMINA ERROR UNDERLYING)
def fix_api(iq):
    try:
        iq.api.digital_underlying_list = {}
        iq.api.get_digital_underlying_list_data = lambda: {"underlying": {}}
        iq.api._IQ_Option__get_digital_open = lambda *args, **kwargs: None
    except:
        pass


# =========================
# 🔥 SOLO FOREX OTC REALES
# =========================
def obtener_pares(iq):

    pares_validos = []

    try:
        activos = iq.get_all_open_time()
    except:
        return []

    for par, data in activos["binary"].items():

        if not data["open"]:
            continue

        if "-OTC" not in par:
            continue

        # 🔥 SOLO FOREX (evita errores)
        if any(x in par for x in [
            "USD", "EUR", "GBP", "JPY", "AUD", "CHF", "CAD"
        ]):
            pares_validos.append(par)

    return pares_validos


def connect():

    while True:
        iq = IQ_Option(IQ_EMAIL, IQ_PASSWORD)
        silent(iq.connect)

        if iq.check_connect():
            fix_api(iq)

            # 🔥 FORZAR BINARIAS
            iq.change_balance("PRACTICE")

            print("🔥 BOT BINARIO ACTIVO")
            send_message("🔥 BOT BINARIO ACTIVO")

            return iq

        time.sleep(5)


def esperar_cierre():
    while int(time.time()) % 60 != 59:
        time.sleep(0.02)


def esperar_apertura():
    while int(time.time()) % 60 != 0:
        time.sleep(0.001)


def resultado(iq, trade_id):

    while True:
        r = silent(iq.check_win_v4, trade_id)

        if r is None:
            time.sleep(1)
            continue

        if isinstance(r, tuple):
            r = r[0]

        try:
            r = float(r)
        except:
            return

        send_message("✅ WIN" if r > 0 else "❌ LOSS")
        return


def ejecutar(iq, par, accion):

    # 🔥 BINARIAS (NO DIGITAL)
    status, trade_id = silent(
        iq.buy, MONTO, par, accion, EXPIRACION
    )

    if not status:
        print(f"❌ No ejecutó {par}")
        return

    send_message(f"📊 {accion.upper()} {par}")

    resultado(iq, trade_id)


# =========================
# 🔥 MAIN
# =========================
def run():

    iq = connect()

    while True:

        esperar_cierre()

        pares = obtener_pares(iq)

        if not pares:
            print("⚠️ No hay pares")
            continue

        print(f"🔍 Analizando {len(pares)} pares...")

        for par in pares:

            señal = detectar_trampa(iq, par)

            if not señal:
                continue

            accion = señal["action"]

            print(f"🎯 {par} {accion}")
            send_message(f"🎯 {accion.upper()} {par}")

            esperar_apertura()

            ejecutar(iq, par, accion)

            break
        else:
            print("⏳ Sin señal...")


if __name__ == "__main__":
    run()
