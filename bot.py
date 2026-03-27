import os
import time
import sys
from iqoptionapi.stable_api import IQ_Option
from strategy import detectar_oportunidad
from telegram_bot import send_message


# ==========================
# SILENCIAR ERRORES
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
MONTO = 1700
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

            # 🔥 ELIMINA ERROR UNDERLYING
            try:
                iq.api.digital_underlying_list = {}
            except:
                pass

            print("✅ BOT ACTIVADO")
            send_message("✅ BOT ACTIVADO")
            return iq

        time.sleep(5)


# ==========================
# OBTENER PARES OTC ABIERTOS
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
# EJECUTAR TRADE
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

    # ❌ BLOQUEAR PAR PROBLEMÁTICO
    pares_bloqueados.add(par)
    send_message(f"⛔ Bloqueado {par}")

    return False


# ==========================
# BOT PRINCIPAL
# ==========================
def run():

    iq = connect()

    while True:

        esperar_cierre()

        pares = get_pairs(iq)

        if not pares:
            print("⚠️ Sin pares disponibles")
            continue

        print(f"🔎 Analizando {len(pares)} pares...")

        mejor_par = None
        mejor_accion = None
        mejor_score = 0

        for par in pares:

            candles = silent(
                iq.get_candles, par, TIMEFRAME, 20, time.time()
            )

            if not candles:
                continue

            accion, score = detectar_oportunidad(candles)

            if accion and score > mejor_score:
                mejor_score = score
                mejor_par = par
                mejor_accion = accion

        if not mejor_par:
            print("⚠️ Sin oportunidad clara")
            continue

        print(f"🎯 MEJOR: {mejor_par} {mejor_accion} ({mejor_score})")
        send_message(f"🎯 {mejor_par} {mejor_accion} (score {mejor_score})")

        # 🔥 ENTRADA EXACTA EN NUEVA VELA
        while int(time.time()) % 60 != 0:
            pass

        ejecutar(iq, mejor_par, mejor_accion)


if __name__ == "__main__":
    run()
