import os
import time
import sys
import requests
from iqoptionapi.stable_api import IQ_Option
from strategy import analyze_market


# ==========================
# 🔥 PARCHE GLOBAL (ANTI DIGITAL ERROR)
# ==========================
from iqoptionapi import stable_api

def fix_digital_bug(iq):
    try:
        iq.api.digital_underlying_list = {}
        iq.api.get_digital_underlying_list_data = lambda x: {"underlying": {}}
        iq.api.subscribe_digital_underlying = lambda *args, **kwargs: None
        iq.api.unsubscribe_digital_underlying = lambda *args, **kwargs: None
    except:
        pass


# ==========================
# TELEGRAM
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
MONTO = 120
EXPIRACION = 1


# ==========================
# CONEXIÓN
# ==========================
def connect():
    while True:
        iq = IQ_Option(IQ_EMAIL, IQ_PASSWORD)
        silent(iq.connect)

        if iq.check_connect():
            fix_digital_bug(iq)  # 🔥 FIX AQUI

            send_message("✅ BOT CONECTADO SIN ERROR DIGITAL")
            return iq

        time.sleep(5)


# ==========================
# OTC ABIERTOS (SOLO BINARY)
# ==========================
def get_otc_abiertos(iq):
    try:
        activos = iq.get_all_open_time()

        return [
            par for par, data in activos["binary"].items()
            if "-OTC" in par and data["open"]
        ]

    except:
        return []


# ==========================
# TIEMPO EXACTO
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
            return "loss"

        if result > 0:
            return "win"
        elif result == 0:
            return "draw"
        else:
            return "loss"


# ==========================
# EJECUCIÓN FORZADA
# ==========================
def ejecutar_trade(iq, pair, action):

    print(f"🚀 Ejecutando {pair} {action}")

    status, trade_id = silent(
        iq.buy, MONTO, pair, action, EXPIRACION
    )

    if not status:
        send_message(f"❌ Broker rechazó {pair}")
        return

    send_message(f"📊 {action.upper()} {pair}")

    resultado = obtener_resultado(iq, trade_id)

    if resultado == "win":
        send_message(f"✅ WIN {pair}")
    else:
        send_message(f"❌ LOSS {pair}")


# ==========================
# BOT
# ==========================
def run():

    iq = connect()

    while True:

        esperar_cierre()

        pares = get_otc_abiertos(iq)

        if not pares:
            print("⚠️ No hay pares OTC abiertos")
            continue

        print(f"🔎 Analizando {len(pares)} pares...")

        for par in pares:

            candles = silent(
                iq.get_candles, par, TIMEFRAME, 70, time.time()
            )

            if not candles:
                continue

            señal = analyze_market(candles, None, None)

            if not señal:
                continue

            action = señal["action"]

            send_message(f"📡 SEÑAL {action.upper()} {par}")

            esperar_apertura()

            ejecutar_trade(iq, par, action)

            break


if __name__ == "__main__":
    run()
