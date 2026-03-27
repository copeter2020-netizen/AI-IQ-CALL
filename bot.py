import os
import time
import sys
from iqoptionapi.stable_api import IQ_Option
from strategy import detectar_senal
from telegram_bot import send_message


# ==========================
# SILENCIAR
# ==========================
class DevNull:
    def write(self, msg): pass
    def flush(self): pass


def silent(func, *args, **kwargs):
    old_stdout = sys.stdout
    old_stderr = sys.stderr
    sys.stdout = DevNull()
    sys.stderr = DevNull()
    try:
        return func(*args, **kwargs)
    except:
        return None
    finally:
        sys.stdout = old_stdout
        sys.stderr = old_stderr


# ==========================
# CONFIG
# ==========================
IQ_EMAIL = os.getenv("IQ_EMAIL")
IQ_PASSWORD = os.getenv("IQ_PASSWORD")

TIMEFRAME = 60
MONTO = 125
EXPIRACION = 1

pares_bloqueados = set()


# ==========================
# CONEXIÓN
# ==========================
def connect():
    while True:
        iq = IQ_Option(IQ_EMAIL, IQ_PASSWORD)
        silent(iq.connect)

        if iq.check_connect():

            try:
                iq.api.digital_underlying_list = {}
            except:
                pass

            print("✅ BOT ACTIVADO")
            send_message("✅ BOT ACTIVADO")
            return iq

        time.sleep(5)


# ==========================
# PARES OTC ABIERTOS
# ==========================
def get_pairs(iq):
    try:
        data = iq.get_all_open_time()

        return [
            p for p, d in data["binary"].items()
            if "-OTC" in p and d["open"] and p not in pares_bloqueados
        ]
    except:
        return []


# ==========================
# ESPERAR CIERRE
# ==========================
def esperar_cierre():
    while int(time.time()) % 60 != 59:
        time.sleep(0.02)


# ==========================
# RESULTADO
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
            send_message("✅ WIN")
        else:
            send_message("❌ LOSS")
        return


# ==========================
# EJECUCIÓN
# ==========================
def ejecutar(iq, par, action):

    for _ in range(3):

        status, trade_id = silent(
            iq.buy, MONTO, par, action, EXPIRACION
        )

        if status:
            print(f"🚀 {par} {action}")
            send_message(f"📊 {action.upper()} {par}")
            resultado(iq, trade_id)
            return True

        time.sleep(0.3)

    # ❌ BLOQUEAR PAR
    pares_bloqueados.add(par)
    send_message(f"⛔ Bloqueado {par}")
    return False


# ==========================
# BOT
# ==========================
def run():

    iq = connect()

    while True:

        esperar_cierre()

        pares = get_pairs(iq)

        if not pares:
            print("⚠️ Sin pares")
            continue

        print(f"🔎 Analizando {len(pares)} pares...")

        for par in pares:

            candles = silent(
                iq.get_candles, par, TIMEFRAME, 10, time.time()
            )

            if not candles:
                continue

            accion = detectar_senal(candles)

            if not accion:
                continue

            print(f"🎯 {par} {accion}")
            send_message(f"📡 {par} {accion}")

            # 🔥 ENTRADA EXACTA
            while int(time.time()) % 60 != 0:
                pass

            if ejecutar(iq, par, accion):
                break

        else:
            print("⚠️ Sin señal")


if __name__ == "__main__":
    run()
