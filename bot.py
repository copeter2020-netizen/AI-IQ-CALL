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
        iq.connect()

        if iq.check_connect():
            print("✅ Conectado")
            return iq

        time.sleep(5)


# 🔥 CLAVE: sincronización REAL con broker
def esperar_siguiente_vela(iq):

    while True:
        server_time = iq.get_server_timestamp()

        # 🔥 entrar en segundo 2 → evita rechazo
        if int(server_time) % 60 == 2:
            break

        time.sleep(0.001)


def esperar_cierre():
    while int(time.time()) % 60 != 59:
        time.sleep(0.01)


def analizar(iq, pair):

    candles = iq.get_candles(pair, TIMEFRAME, 30, time.time())

    if not candles:
        return None

    return analyze_market(candles, None, None)


# 🔥 EJECUCIÓN REAL SIN RECHAZO
def ejecutar(iq, pair, action):

    print(f"🚀 Ejecutando {pair}")

    # 🔥 USAR BINARY (NO digital → menos rechazo en pares normales)
    status, trade_id = iq.buy(MONTO, pair, action, EXPIRACION)

    if not status:
        print("❌ Broker rechazó")
        return None

    print("✅ Entrada realizada")
    return trade_id


def resultado(iq, trade_id):

    while True:
        result = iq.check_win_v4(trade_id)

        if result is None:
            time.sleep(1)
            continue

        if isinstance(result, tuple):
            result = result[0]

        return float(result)


def run():

    iq = connect()

    while True:

        print("⏳ Esperando cierre vela...")
        esperar_cierre()

        mejor = None
        mejor_pair = None
        mejor_score = 0

        for pair in PARES:

            señal = analizar(iq, pair)

            if not señal:
                continue

            if señal["score"] > mejor_score:
                mejor_score = señal["score"]
                mejor = señal
                mejor_pair = pair

        if not mejor:
            print("⚠️ Sin señal")
            continue

        print(f"📡 Señal en {mejor_pair}")

        # 🔥 sincronización correcta
        esperar_siguiente_vela(iq)

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
