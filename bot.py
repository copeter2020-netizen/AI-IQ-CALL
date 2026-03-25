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
MONTO = 15500
EXPIRACION = 1

PARES = [
    "EURUSD",
    "USDJPY",
    "EURJPY"
]


def connect():
    while True:
        iq = IQ_Option(IQ_EMAIL, IQ_PASSWORD)
        silent(iq.connect)

        if iq.check_connect():
            print("✅ Conectado")
            return iq
        time.sleep(5)


# 🔥 ESPERA CIERRE VELA
def esperar_cierre():
    while int(time.time()) % 60 != 59:
        time.sleep(0.01)


# 🔥 ENTRADA REAL (SEGUNDO 1 → EVITA RECHAZO)
def esperar_entrada_real(iq):
    while True:
        t = iq.get_server_timestamp()

        # 👉 entra en segundo 1 (NO en 0)
        if int(t) % 60 == 1:
            break

        time.sleep(0.001)


def analizar(iq, pair):

    candles = silent(
        iq.get_candles, pair, TIMEFRAME, 30, time.time()
    )

    if not candles or len(candles) < 30:
        return None

    return analyze_market(candles, None, None)


def ejecutar_operacion(iq, pair, action):

    print(f"🚀 Entrada en {pair}")

    data = silent(iq.buy, MONTO, pair, action, EXPIRACION)

    if not data or not isinstance(data, tuple):
        print("❌ Fallo ejecución")
        return None

    status, trade_id = data

    if not status:
        print("❌ Entrada rechazada (broker)")
        return None

    print("✅ Entrada confirmada")
    return trade_id


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


def run():

    iq = connect()

    while True:

        print("⏳ Esperando cierre...")
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

        print(f"📡 Señal en {mejor_pair}")

        # 🔥 ENTRADA REAL CORREGIDA
        esperar_entrada_real(iq)

        send_message(
            f"📊 CALL {mejor_pair}\n⏱ 1m\n📊 Score: {mejor_score}\n🟢 Entrada válida"
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
