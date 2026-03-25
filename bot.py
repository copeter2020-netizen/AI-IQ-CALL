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
    "EURUSD","GBPUSD","USDJPY","AUDUSD",
    "USDCAD","USDCHF","EURGBP","EURJPY"
]


# ==========================
# CONEXIÓN (SIN DIGITAL)
# ==========================
def connect():
    while True:
        iq = IQ_Option(IQ_EMAIL, IQ_PASSWORD)

        # 🔥 BLOQUEO DIGITAL
        try:
            iq.api.digital_thread = None
            iq.api.get_digital_underlying_list_data = lambda *a, **k: {"underlying": []}
        except:
            pass

        iq.connect()

        if iq.check_connect():
            print("✅ Conectado")
            send_message("✅ BOT ACTIVO")
            return iq

        time.sleep(5)


# ==========================
# PARES ABIERTOS REALES
# ==========================
def get_open_pairs(iq):

    try:
        assets = iq.get_all_open_time()
        abiertos = []

        for par in PARES:
            if par in assets["binary"] and assets["binary"][par]["open"]:
                abiertos.append(par)

        return abiertos

    except:
        return []


# ==========================
# TIEMPO EXACTO
# ==========================
def esperar_cierre():
    while int(time.time()) % 60 != 59:
        time.sleep(0.05)


def esperar_entrada():
    while int(time.time()) % 60 != 0:
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
# EJECUCIÓN REAL (CLAVE)
# ==========================
def ejecutar(iq, pair, action):

    print(f"🚀 Intentando {pair} {action}")

    # 🔥 VALIDAR JUSTO ANTES DE ENTRAR
    try:
        assets = iq.get_all_open_time()
        if not assets["binary"][pair]["open"]:
            print("⚠️ Par cerrado en ese segundo")
            return None
    except:
        return None

    # 🔥 REINTENTO INTELIGENTE
    for _ in range(3):

        try:
            status, trade_id = iq.buy(MONTO, pair, action, EXPIRACION)

            if status:
                send_message(f"🚀 {pair} {action}")
                break

        except:
            pass

        time.sleep(0.2)

    else:
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
# BOT
# ==========================
def run():

    iq = connect()

    while True:

        print("⏳ Esperando cierre vela...")
        esperar_cierre()

        pares = get_open_pairs(iq)

        if not pares:
            print("⚠️ No hay pares abiertos")
            continue

        print(f"🔎 Analizando {len(pares)} pares...")

        for pair in pares:

            señal = analizar(iq, pair)

            if not señal:
                continue

            action = señal["action"]
            score = señal["score"]

            print(f"📡 SEÑAL {pair} {action} ({score})")
            send_message(f"📡 {pair} {action} | Score {score}")

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
