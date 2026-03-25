import os
import time
import sys
import requests
from iqoptionapi.stable_api import IQ_Option
from strategy import analyze_market


# ==========================
# TELEGRAM DIRECTO (SIN ARCHIVO)
# ==========================
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_message(text):
    try:
        if TOKEN and CHAT_ID:
            requests.post(
                f"https://api.telegram.org/bot{TOKEN}/sendMessage",
                data={"chat_id": CHAT_ID, "text": text},
                timeout=5
            )
    except:
        pass


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
IQ_EMAIL = os.getenv("IQ_EMAIL")
IQ_PASSWORD = os.getenv("IQ_PASSWORD")

TIMEFRAME = 60
MONTO = 2545
EXPIRACION = 1

PARES = [
    "EURUSD",
    "GBPUSD",
    "USDJPY",
    "AUDUSD",
    "USDCAD",
    "USDCHF",
    "EURGBP",
    "EURJPY"
]


# ==========================
# CONEXIÓN
# ==========================
def connect():
    while True:
        iq = IQ_Option(IQ_EMAIL, IQ_PASSWORD)
        iq.connect()

        if iq.check_connect():
            print("✅ Conectado")
            send_message("✅ BOT CONECTADO")
            return iq
        time.sleep(5)


# ==========================
# PARES ABIERTOS (FIX REAL)
# ==========================
def get_open_pairs(iq):

    try:
        assets = iq.get_all_open_time()
    except:
        return PARES  # fallback

    activos = []

    for par in PARES:
        try:
            if assets["binary"][par]["open"]:
                activos.append(par)
        except:
            activos.append(par)  # 🔥 FORZAR análisis aunque falle API

    return activos if activos else PARES


# ==========================
# TIEMPO EXACTO
# ==========================
def esperar_cierre():
    while int(time.time()) % 60 != 59:
        time.sleep(0.05)


def esperar_apertura():
    while int(time.time()) % 60 != 0:
        time.sleep(0.01)


# ==========================
# ANALIZAR (SIN BLOQUEOS)
# ==========================
def analizar(iq, pair):

    candles = iq.get_candles(pair, TIMEFRAME, 30, time.time())

    if not candles:
        return None

    señal = analyze_market(candles, None, None)

    return señal


# ==========================
# EJECUCIÓN REAL (FIX BROKER)
# ==========================
def ejecutar(iq, pair, action):

    print(f"🚀 Ejecutando {pair} {action}")
    send_message(f"🚀 Ejecutando {pair} {action}")

    status, trade_id = iq.buy(MONTO, pair, action, EXPIRACION)

    if not status:
        print("❌ Broker rechazó")
        send_message("❌ Broker rechazó entrada")
        return None

    while True:
        result = iq.check_win_v4(trade_id)

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

        print("⏳ Esperando cierre vela...")
        esperar_cierre()

        pares = get_open_pairs(iq)

        print(f"🔎 Analizando {len(pares)} pares...")

        for pair in pares:

            señal = analizar(iq, pair)

            if not señal:
                continue

            action = señal["action"]
            score = señal["score"]

            print(f"📡 SEÑAL {pair} {action} (score {score})")

            # 🔥 ENVÍA SIEMPRE MENSAJE
            send_message(f"📡 SEÑAL {pair} {action} | Score {score}")

            # 🔥 ESPERA SIGUIENTE VELA
            esperar_apertura()

            resultado = ejecutar(iq, pair, action)

            if resultado is None:
                continue

            if resultado > 0:
                print("✅ WIN")
                send_message("✅ WIN")
            else:
                print("❌ LOSS")
                send_message("❌ LOSS")

            break  # 🔥 SOLO UNA OPERACIÓN POR VELA


if __name__ == "__main__":
    run()
