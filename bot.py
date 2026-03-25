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


# ==========================
# CONEXIÓN + BALANCE
# ==========================
def connect():
    while True:
        iq = IQ_Option(IQ_EMAIL, IQ_PASSWORD)
        iq.connect()

        if iq.check_connect():
            print("✅ Conectado")

            # 🔥 IMPORTANTE → usar balance real o practice
            iq.change_balance("PRACTICE")  # o "REAL"

            return iq

        time.sleep(5)


# ==========================
# VALIDAR PAR ABIERTO
# ==========================
def par_abierto(iq, pair):
    assets = iq.get_all_open_time()

    try:
        return assets["binary"][pair]["open"]
    except:
        return False


# ==========================
# SINCRONIZACIÓN REAL
# ==========================
def esperar_entrada(iq):

    while True:
        server_time = iq.get_server_timestamp()

        # 🔥 ventana válida real (segundos 2–4)
        if 2 <= int(server_time) % 60 <= 4:
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
# EJECUCIÓN ROBUSTA
# ==========================
def ejecutar(iq, pair, action):

    # 🔥 validar que el par esté abierto
    if not par_abierto(iq, pair):
        print(f"⚠️ {pair} cerrado")
        return None

    print(f"🚀 Ejecutando {pair}")

    status, trade_id = iq.buy(MONTO, pair, action, EXPIRACION)

    if not status:
        print("❌ Broker rechazó (retry digital)")

        # 🔥 fallback automático a digital
        trade_id = iq.buy_digital_spot(pair, MONTO, action, EXPIRACION)

        if not trade_id:
            print("❌ También falló digital")
            return None

    print("✅ Entrada realizada")
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

        return float(result)


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

        print(f"🔎 Analizando {len(PARES)} pares...")

        for pair in PARES:

            if not par_abierto(iq, pair):
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

        # 🔥 entrada correcta
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
