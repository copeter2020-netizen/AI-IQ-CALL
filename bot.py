import os
import time
import requests
from iqoptionapi.stable_api import IQ_Option
from strategy import analyze_market


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
# CONFIG
# ==========================
IQ_EMAIL = os.getenv("IQ_EMAIL")
IQ_PASSWORD = os.getenv("IQ_PASSWORD")

TIMEFRAME = 60
MONTO = 7000
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
# CONEXIÓN (FIX DEFINITIVO DIGITAL)
# ==========================
def connect():
    while True:
        iq = IQ_Option(IQ_EMAIL, IQ_PASSWORD)

        # 🔥 BLOQUEO TOTAL DEL DIGITAL (ANTES DE CONECTAR)
        try:
            iq.api.digital_thread = None
            iq.api.get_digital_open = lambda *args, **kwargs: None
            iq.api.get_digital_underlying_list_data = lambda *args, **kwargs: {"underlying": []}
            iq.api.subscribe_digital = lambda *args, **kwargs: None
            iq.api.unsubscribe_digital = lambda *args, **kwargs: None
        except:
            pass

        iq.connect()

        if iq.check_connect():
            print("✅ Conectado")
            send_message("✅ BOT ACTIVO")
            return iq

        time.sleep(5)


# ==========================
# TIEMPO
# ==========================
def esperar_cierre():
    while int(time.time()) % 60 != 59:
        time.sleep(0.05)


def esperar_entrada():
    while True:
        if int(time.time()) % 60 == 0:
            break
        time.sleep(0.001)


# ==========================
# ANALIZAR
# ==========================
def analizar(iq, pair):
    try:
        candles = iq.get_candles(pair, TIMEFRAME, 30, time.time())
        if not candles:
            return None
        return analyze_market(candles, None, None)
    except:
        return None


# ==========================
# EJECUCIÓN FORZADA REAL
# ==========================
def ejecutar(iq, pair, action):

    print(f"🚀 EJECUTANDO {pair} {action}")
    send_message(f"🚀 {pair} {action}")

    trade_id = None

    try:
        status, trade_id = iq.buy(MONTO, pair, action, EXPIRACION)
    except Exception as e:
        print("❌ Error ejecución:", e)
        return None

    if not status:
        print("❌ Broker rechazó")
        return None

    # ==========================
    # RESULTADO
    # ==========================
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

        print("🔎 Analizando pares...")

        for pair in PARES:

            señal = analizar(iq, pair)

            if not señal:
                continue

            action = señal["action"]
            score = señal["score"]

            print(f"📡 SEÑAL {pair} {action} ({score})")
            send_message(f"📡 {pair} {action} | Score {score}")

            # 🔥 ENTRADA EXACTA EN NUEVA VELA
            esperar_entrada()

            resultado = ejecutar(iq, pair, action)

            if resultado is None:
                continue

            if resultado > 0:
                print("✅ WIN")
                send_message("✅ WIN")
            else:
                print("❌ LOSS")
                send_message("❌ LOSS")

            break


if __name__ == "__main__":
    run()
