import os
import time
import sys
from iqoptionapi.stable_api import IQ_Option
from strategy import analizar_price_action
from telegram_bot import send_message


# ==========================
# SILENCIO
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
MONTO = 75
EXPIRACION = 1

bloqueados = set()


# ==========================
# CONEXIÓN REAL
# ==========================
def connect():
    while True:
        iq = IQ_Option(IQ_EMAIL, IQ_PASSWORD)
        silent(iq.connect)

        if iq.check_connect():

            # 🔥 eliminar error digital
            try:
                iq.api.digital_underlying_list = {}
            except:
                pass

            print("✅ BOT CONECTADO AL GRÁFICO")
            send_message("✅ BOT CONECTADO AL GRÁFICO")
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
            if "-OTC" in p and d["open"] and p not in bloqueados
        ]
    except:
        return []


# ==========================
# ESPERAR VELA
# ==========================
def esperar_cierre():
    while int(time.time()) % 60 != 59:
        time.sleep(0.02)


def esperar_apertura():
    while int(time.time()) % 60 != 0:
        time.sleep(0.001)


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
# EJECUTAR
# ==========================
def ejecutar(iq, par, accion):

    for _ in range(3):

        status, trade_id = silent(
            iq.buy, MONTO, par, accion, EXPIRACION
        )

        if status:
            print(f"🚀 {par} {accion}")
            send_message(f"📊 {accion.upper()} {par}")
            resultado(iq, trade_id)
            return True

        time.sleep(0.3)

    bloqueados.add(par)
    send_message(f"⛔ {par} bloqueado")

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

        mejor = None
        mejor_score = 0

        for par in pares:

            candles = silent(
                iq.get_candles, par, TIMEFRAME, 30, time.time()
            )

            if not candles:
                continue

            señal = analizar_price_action(candles)

            if not señal:
                continue

            if señal["score"] > mejor_score:
                mejor = (par, señal)
                mejor_score = señal["score"]

        if not mejor:
            print("⚠️ Sin oportunidad real")
            continue

        par, señal = mejor

        print(f"🎯 {par} {señal['action']} ({señal['score']})")
        send_message(f"🎯 {par} {señal['action']}")

        esperar_apertura()

        ejecutar(iq, par, señal["action"])


if __name__ == "__main__":
    run()
