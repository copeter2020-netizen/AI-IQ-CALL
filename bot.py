import os
import time
import sys
from iqoptionapi.stable_api import IQ_Option
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
IQ_EMAIL = os.environ.get("IQ_EMAIL")
IQ_PASSWORD = os.environ.get("IQ_PASSWORD")

TIMEFRAME = 60
MONTO = 112
EXPIRACION = 1

# 🔥 PARES BLOQUEADOS AUTOMÁTICAMENTE
pares_bloqueados = set()


# ==========================
# CONEXIÓN
# ==========================
def connect():
    while True:
        iq = IQ_Option(IQ_EMAIL, IQ_PASSWORD)
        silent(iq.connect)

        if iq.check_connect():
            print("✅ BOT ACTIVADO")

            # 🔥 BLOQUEAR DIGITAL (SOLUCIÓN ERROR UNDERLYING)
            try:
                iq.api.digital_underlying_list = {}
            except:
                pass

            send_message("✅ BOT ACTIVADO")
            return iq

        time.sleep(5)


# ==========================
# OBTENER OTC ABIERTOS
# ==========================
def get_otc_abiertos(iq):
    try:
        activos = iq.get_all_open_time()

        return [
            par for par, data in activos["binary"].items()
            if "-OTC" in par and data["open"]
            and par not in pares_bloqueados
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
def obtener_resultado(iq, trade_id):

    while True:
        result = silent(iq.check_win_v4, trade_id)

        if result is None:
            time.sleep(1)
            continue

        try:
            if isinstance(result, tuple):
                result = result[0]

            result = float(result)
        except:
            return

        if result > 0:
            send_message("✅ WIN")
        else:
            send_message("❌ LOSS")

        return


# ==========================
# EJECUCIÓN INTELIGENTE
# ==========================
def ejecutar(iq, par, action):

    for intento in range(3):

        status, trade_id = silent(
            iq.buy, MONTO, par, action, EXPIRACION
        )

        if status:
            print(f"🚀 {par} {action}")
            send_message(f"📊 {action.upper()} {par}")

            obtener_resultado(iq, trade_id)
            return True

        time.sleep(0.3)

    # ❌ SI FALLA → BLOQUEAR PAR
    print(f"⛔ Bloqueando {par}")
    send_message(f"⛔ Par bloqueado {par}")

    pares_bloqueados.add(par)

    return False


# ==========================
# ESTRATEGIA SIMPLE
# ==========================
def detectar_senal(candles):

    if len(candles) < 3:
        return None

    c1 = candles[-1]
    c2 = candles[-2]

    # CALL
    if c2["close"] < c2["open"] and c1["close"] > c1["open"]:
        return "call"

    # PUT
    if c2["close"] > c2["open"] and c1["close"] < c1["open"]:
        return "put"

    return None


# ==========================
# BOT PRINCIPAL
# ==========================
def run():

    iq = connect()

    while True:

        esperar_cierre()

        pares = get_otc_abiertos(iq)

        if not pares:
            print("⚠️ Sin pares válidos")
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

            print(f"🎯 SEÑAL {par} {accion}")
            send_message(f"📡 {par} {accion}")

            # 🔥 ENTRADA EXACTA
            while int(time.time()) % 60 != 0:
                pass

            ejecutado = ejecutar(iq, par, accion)

            if ejecutado:
                break

        else:
            print("⚠️ Sin señal válida")


# ==========================
# START
# ==========================
if __name__ == "__main__":
    run()
