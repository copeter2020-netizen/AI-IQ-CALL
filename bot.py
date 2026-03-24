import os
import time
import sys
from iqoptionapi.stable_api import IQ_Option
from strategy import analyze_market
from telegram_bot import send_message


# ==========================
# SILENCIAR LOGS
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
MONTO = 2545
EXPIRACION = 1

PARES = [
    "EURUSD",
    "GBPUSD",
    "USDJPY",
    "AUDUSD",
    "EURGBP",
    "EURJPY"
]


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
        else:
            time.sleep(5)


# ==========================
# FILTRAR PARES (FIX)
# ==========================
def get_open_pairs(iq):

    assets = silent(iq.get_all_open_time)

    # 🔥 SI FALLA → USA TODOS LOS PARES
    if not assets or "binary" not in assets:
        return PARES

    activos = []

    for par in PARES:
        try:
            if par in assets["binary"] and assets["binary"][par]["open"]:
                activos.append(par)
        except:
            continue

    # 🔥 SI NO HAY ABIERTOS → USA TODOS IGUAL
    if not activos:
        return PARES

    return activos


# ==========================
# TIEMPO
# ==========================
def esperar_cierre():
    while int(time.time()) % 60 != 59:
        time.sleep(0.05)


def esperar_apertura():
    while int(time.time()) % 60 != 0:
        time.sleep(0.01)


# ==========================
# CONTINUIDAD
# ==========================
def contar_color(candles):
    count = 0
    tipo = None

    for i in range(len(candles)-1, -1, -1):
        c = candles[i]

        if c["close"] > c["open"]:
            if tipo in [None, "verde"]:
                tipo = "verde"
                count += 1
            else:
                break

        elif c["close"] < c["open"]:
            if tipo in [None, "roja"]:
                tipo = "roja"
                count += 1
            else:
                break
        else:
            break

    return tipo, count


# ==========================
# ANALIZAR
# ==========================
def analizar(iq, pair):

    candles = silent(
        iq.get_candles, pair, TIMEFRAME, 30, time.time()
    )

    if not candles or len(candles) < 30:
        return None

    tipo, count = contar_color(candles)

    if count < 2 or count > 3:
        return None

    return analyze_market(candles, None, None)


# ==========================
# EJECUTAR OPERACIÓN
# ==========================
def ejecutar_operacion(iq, pair, action):

    status = False
    trade_id = None

    for _ in range(3):
        data = silent(iq.buy, MONTO, pair, action, EXPIRACION)

        if data and isinstance(data, tuple):
            status, trade_id = data

        if status:
            break

        time.sleep(1)

    if not status:
        return None

    while True:
        result = silent(iq.check_win_v4, trade_id)

        if result is None:
            time.sleep(1)
            continue

        if isinstance(result, tuple):
            result = result[0]

        if isinstance(result, str):
            try:
                result = float(result)
            except:
                result = 0

        return result


# ==========================
# BOT PRINCIPAL
# ==========================
def run():

    iq = connect()

    while True:

        print("⏳ Esperando cierre de vela...")
        esperar_cierre()

        pares = get_open_pairs(iq)

        print(f"🔎 Analizando {len(pares)} pares...")

        mejor = None
        mejor_pair = None
        mejor_score = 0

        for pair in pares:

            señal = analizar(iq, pair)

            if not señal:
                continue

            if señal["score"] > mejor_score:
                mejor_score = señal["score"]
                mejor = señal
                mejor_pair = pair

        if not mejor:
            print("⚠️ Sin señal válida")
            continue

        action = mejor["action"]

        print(f"📡 Señal detectada en {mejor_pair} ({action})")

        print("⏭ Esperando siguiente vela...")
        esperar_apertura()

        send_message(
            f"📊 {action.upper()} {mejor_pair}\n⏱ 1m\n📊 Score: {mejor_score}\n🚀 Entrada en siguiente vela"
        )

        resultado = ejecutar_operacion(iq, mejor_pair, action)

        if resultado is None:
            print("❌ Error al ejecutar operación")
            continue

        if resultado > 0:
            print("✅ WIN")
            send_message("✅ WIN")
        else:
            print("❌ LOSS")
            send_message("❌ LOSS")


if __name__ == "__main__":
    run()
