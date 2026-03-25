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
MONTO = 5000
EXPIRACION = 1

PARES = [
    "EURUSD","GBPUSD","USDJPY","AUDUSD",
    "USDCAD","USDCHF","EURGBP","EURJPY"
]


# ==========================
# CONEXIÓN (BLOQUEO TOTAL DIGITAL)
# ==========================
def connect():
    while True:
        iq = IQ_Option(IQ_EMAIL, IQ_PASSWORD)
        iq.connect()

        if iq.check_connect():
            print("✅ Conectado")

            # 🔥 BLOQUEO AGRESIVO DIGITAL (ERROR UNDERLYING)
            try:
                iq.api.digital_underlying_list = {}
                iq.api.get_digital_underlying_list_data = lambda: {}
                iq.api.subscribe_digital = lambda *args, **kwargs: None
                iq.api.get_digital_open = lambda *args, **kwargs: None
                iq.api.get_digital_payout = lambda *args, **kwargs: 0
            except:
                pass

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
    while int(time.time()) % 60 != 1:
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
# EJECUCIÓN FORZADA
# ==========================
def ejecutar(iq, pair, action):

    print(f"🚀 FORZANDO ENTRADA {pair} {action}")
    send_message(f"🚀 ENTRADA {pair} {action}")

    trade_id = None

    # 🔥 INTENTO DIRECTO SIN VALIDACIONES
    for i in range(2):
        try:
            status, trade_id = iq.buy(MONTO, pair, action, EXPIRACION)

            if status:
                break

        except:
            pass

        time.sleep(0.2)

    if not trade_id:
        print("❌ No se pudo ejecutar")
        send_message("❌ No ejecutó")
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
# BOT
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

            # 🔥 ENTRADA INMEDIATA SIGUIENTE VELA
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
