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
    try:
        return func(*args, **kwargs)
    except:
        return None


# ==========================
# CONFIG
# ==========================
IQ_EMAIL = os.environ.get("IQ_EMAIL")
IQ_PASSWORD = os.environ.get("IQ_PASSWORD")

TIMEFRAME = 60
MONTO = 5000
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

            # 🔥 IMPORTANTE: tipo de cuenta
            iq.change_balance("PRACTICE")  # o "REAL"

            return iq

        time.sleep(5)


# ==========================
# VALIDAR ACTIVO BINARY
# ==========================
def activo_disponible(iq, pair):

    assets = iq.get_all_open_time()

    try:
        return assets["binary"][pair]["open"]
    except:
        return False


# ==========================
# SINCRONIZACIÓN EXACTA
# ==========================
def esperar_entrada(iq):

    while True:
        t = iq.get_server_timestamp()

        # 🔥 ventana exacta para binary (clave)
        if 2 <= int(t) % 60 <= 3:
            break

        time.sleep(0.001)


def esperar_cierre():
    while int(time.time()) % 60 != 59:
        time.sleep(0.01)


# ==========================
# ANALIZAR
# ==========================
def analizar(iq, pair):

    candles = iq.get_candles(pair, TIMEFRAME, 30, time.time())

    if not candles:
        return None

    return analyze_market(candles, None, None)


# ==========================
# EJECUCIÓN BINARY PURA
# ==========================
def ejecutar(iq, pair, action):

    print(f"🚀 Ejecutando {pair}")

    status, trade_id = iq.buy(MONTO, pair, action, EXPIRACION)

    if not status:
        print("❌ Broker rechazó (binary)")
        return None

    print("✅ Entrada binary OK")
    return trade_id


# ==========================
# RESULTADO
# ==========================
def resultado(iq, trade_id):

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

        mejor = None
        mejor_pair = None
        mejor_score = 0

        print("🔎 Analizando pares...")

        for pair in PARES:

            if not activo_disponible(iq, pair):
                continue

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

        print(f"📡 Señal en {mejor_pair}")

        # 🔥 sincronización exacta
        esperar_entrada(iq)

        send_message(
            f"📈 CALL {mejor_pair}\n⏱ 1m\n📊 Score: {mejor_score}"
        )

        trade_id = ejecutar(iq, mejor_pair, "call")

        if not trade_id:
            continue

        res = resultado(iq, trade_id)

        if res > 0:
            print("✅ WIN")
            send_message("✅ WIN")
        else:
            print("❌ LOSS")
            send_message("❌ LOSS")


if __name__ == "__main__":
    run()
