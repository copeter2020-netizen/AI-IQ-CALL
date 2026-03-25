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
    "EURUSD",
    "GBPUSD",
    "USDJPY",
    "AUDUSD",
    "USDCHF",
    "EURGBP",
    "EURJPY"
]


# ==========================
# CONEXIÓN (FIX DIGITAL)
# ==========================
def connect():
    while True:
        iq = IQ_Option(IQ_EMAIL, IQ_PASSWORD)
        iq.connect()

        if iq.check_connect():
            print("✅ Conectado")

            # 🔥 BLOQUEO TOTAL DIGITAL
            try:
                iq.api.digital_underlying_list = {}
                iq.api.get_digital_underlying_list_data = lambda: {}
                iq.api.subscribe_digital = lambda *args, **kwargs: None
                iq.api.get_digital_open = lambda *args, **kwargs: None
            except:
                pass

            send_message("✅ BOT CONECTADO")
            return iq

        time.sleep(5)


# ==========================
# PARES ABIERTOS (FIX 0 PARES)
# ==========================
def get_open_pairs(iq):

    try:
        assets = iq.get_all_open_time()
        abiertos = []

        for par in PARES:
            try:
                if (
                    par in assets["binary"]
                    and assets["binary"][par]["open"]
                ):
                    abiertos.append(par)
            except:
                continue

        # 🔥 SI FALLA → USAR LISTA
        if not abiertos:
            print("⚠️ Broker no respondió, usando lista fija")
            return PARES

        return abiertos

    except:
        print("⚠️ Error obteniendo pares, usando lista fija")
        return PARES


# ==========================
# TIEMPO
# ==========================
def esperar_cierre():
    while int(time.time()) % 60 != 59:
        time.sleep(0.05)


def esperar_entrada_exacta(iq):
    while True:
        server_time = iq.get_server_timestamp()

        if int(server_time) % 60 == 2:
            break

        time.sleep(0.002)


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
# EJECUCIÓN
# ==========================
def ejecutar(iq, pair, action):

    print(f"🚀 Ejecutando {pair} {action}")

    # 🔥 VALIDAR ACTIVO EN TIEMPO REAL
    try:
        check = iq.get_all_open_time()
        if not check["binary"][pair]["open"]:
            print("⚠️ Par cerrado justo ahora")
            return None
    except:
        pass

    try:
        status, trade_id = iq.buy(MONTO, pair, action, EXPIRACION)
        time.sleep(0.3)

    except Exception as e:
        print("❌ Error ejecución:", e)
        send_message("❌ Error ejecución")
        return None

    if not status:
        print("❌ Broker rechazó")
        send_message("❌ Broker rechazó")
        return None

    send_message(f"🚀 {pair} {action}")

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

        pares = get_open_pairs(iq)

        print(f"🔎 Analizando {len(pares)} pares...")

        for pair in pares:

            señal = analizar(iq, pair)

            if not señal:
                continue

            action = señal["action"]
            score = señal["score"]

            print(f"📡 SEÑAL {pair} {action} ({score})")
            send_message(f"📡 {pair} {action} | Score {score}")

            # 🔥 ENTRADA EXACTA
            esperar_entrada_exacta(iq)

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
