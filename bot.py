import os
import time
import sys
from iqoptionapi.stable_api import IQ_Option
from strategy import analyze_market
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
MONTO = 10000
EXPIRACION = 1

PAR = "EURUSD-OTC"


# ==========================
# CONEXIÓN
# ==========================
def connect():
    while True:
        iq = IQ_Option(IQ_EMAIL, IQ_PASSWORD)
        silent(iq.connect)

        if iq.check_connect():
            print("✅ Conectado")
            return iq

        time.sleep(5)


# ==========================
# TIEMPO EXACTO
# ==========================
def esperar_cierre():
    while int(time.time()) % 60 != 59:
        time.sleep(0.03)


def esperar_apertura_pro():
    while True:
        t = time.time()
        if int(t) % 60 == 0 and (t - int(t)) < 0.2:
            break


# ==========================
# ANALIZAR
# ==========================
def analizar(iq):

    candles = silent(
        iq.get_candles, PAR, TIMEFRAME, 30, time.time()
    )

    if not candles:
        return None

    return analyze_market(candles, None, None)


# ==========================
# EJECUCIÓN FORZADA
# ==========================
def ejecutar(iq, action):

    # 🔥 solo CALL
    action = "call"

    print("🚀 EJECUTANDO CALL")
    send_message(f"🚀 CALL {PAR}")

    status, trade_id = silent(
        iq.buy, MONTO, PAR, action, EXPIRACION
    )

    if not status:
        print("❌ Broker rechazó")
        return None

    # ==========================
    # RESULTADO FIX TOTAL
    # ==========================
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
            result = 0

        return result


# ==========================
# BOT
# ==========================
def run():

    iq = connect()

    while True:

        print("⏳ Esperando cierre vela...")
        esperar_cierre()

        señal = analizar(iq)

        if not señal:
            print("⚠️ Sin señal institucional...")
            continue

        score = señal["score"]

        print(f"🎯 CALL INSTITUCIONAL | score {score}")

        # 🔥 ENTRADA EXACTA
        esperar_apertura_pro()

        send_message(
            f"📊 CALL {PAR}\n⏱ 1m\n🏦 MODO INSTITUCIONAL\n📊 Score: {score}"
        )

        resultado = ejecutar(iq, "call")

        if resultado is None:
            continue

        if resultado > 0:
            print("✅ WIN")
            send_message("✅ WIN")
        else:
            print("❌ LOSS")
            send_message("❌ LOSS")


if __name__ == "__main__":
    run()
