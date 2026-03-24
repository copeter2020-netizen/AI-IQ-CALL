import os
import time
import sys
from iqoptionapi.stable_api import IQ_Option
from strategy import analyze_market
from telegram_bot import send_message


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


IQ_EMAIL = os.environ.get("IQ_EMAIL")
IQ_PASSWORD = os.environ.get("IQ_PASSWORD")

TIMEFRAME = 60
MONTO = 15000
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
        time.sleep(5)


# ==========================
# ESPERAR CIERRE
# ==========================
def esperar_cierre():
    while int(time.time()) % 60 != 59:
        time.sleep(0.01)


# ==========================
# ENTRADA EN SIGUIENTE VELA
# ==========================
def esperar_siguiente_vela(iq):
    while True:
        t = iq.get_server_timestamp()
        if int(t) % 60 == 0:
            break
        time.sleep(0.001)


# ==========================
# ANALIZAR
# ==========================
def analizar(iq, pair):

    candles = silent(
        iq.get_candles, pair, TIMEFRAME, 30, time.time()
    )

    if not candles or len(candles) < 30:
        return None

    return analyze_market(candles, None, None)


# ==========================
# EJECUTAR OPERACIÓN (1 INTENTO)
# ==========================
def ejecutar_operacion(iq, pair, action):

    print(f"🚀 Entrada en {pair}...")

    data = silent(iq.buy, MONTO, pair, action, EXPIRACION)

    if not data or not isinstance(data, tuple):
        print("❌ No entró (sin reintentos)")
        return None

    status, trade_id = data

    if not status:
        print("❌ Entrada rechazada")
        return None

    print("✅ Entrada realizada")
    return trade_id


# ==========================
# RESULTADO
# ==========================
def verificar_resultado(iq, trade_id):

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

        mejor = None
        mejor_pair = None
        mejor_score = 0

        print(f"🔎 Analizando {len(PARES)} pares...")

        for pair in PARES:

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

        print(f"📡 Señal en {mejor_pair} ({action})")

        # 🔥 ENTRADA SIGUIENTE VELA
        esperar_siguiente_vela(iq)

        send_message(
            f"📊 {action.upper()} {mejor_pair}\n⏱ 1m\n📊 Score: {mejor_score}\n🎯 Entrada siguiente vela"
        )

        trade_id = ejecutar_operacion(iq, mejor_pair, action)

        if not trade_id:
            continue

        resultado = verificar_resultado(iq, trade_id)

        if resultado > 0:
            print("✅ WIN")
            send_message("✅ WIN")
        else:
            print("❌ LOSS")
            send_message("❌ LOSS")


if __name__ == "__main__":
    run()
