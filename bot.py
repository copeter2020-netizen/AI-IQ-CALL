import os
import time
import sys
from iqoptionapi.stable_api import IQ_Option
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
MONTO = 85
EXPIRACION = 1


def connect():
    while True:
        iq = IQ_Option(IQ_EMAIL, IQ_PASSWORD)
        silent(iq.connect)

        if iq.check_connect():
            print("✅ Conectado")
            send_message("✅ BOT ACTIVO")
            return iq

        time.sleep(5)


def get_otc_abiertos(iq):
    try:
        activos = iq.get_all_open_time()
        return [
            par for par, data in activos["binary"].items()
            if "-OTC" in par and data["open"]
        ]
    except:
        return []


def esperar_cierre():
    while int(time.time()) % 60 != 59:
        time.sleep(0.02)


def esperar_apertura():
    while int(time.time()) % 60 != 0:
        time.sleep(0.001)


# ==========================
# 🔥 SOPORTE Y RESISTENCIA
# ==========================
def detectar_niveles(candles):

    soportes = []
    resistencias = []

    for i in range(2, len(candles)-2):

        c = candles[i]

        # soporte (mínimo local)
        if (
            c["min"] < candles[i-1]["min"] and
            c["min"] < candles[i+1]["min"]
        ):
            soportes.append(c["min"])

        # resistencia (máximo local)
        if (
            c["max"] > candles[i-1]["max"] and
            c["max"] > candles[i+1]["max"]
        ):
            resistencias.append(c["max"])

    return soportes[-3:], resistencias[-3:]


# ==========================
# 🔥 PATRÓN ROJA → VERDE
# ==========================
def patron_roja_verde(candles):

    if len(candles) < 3:
        return False

    c1 = candles[-1]
    c2 = candles[-2]

    return (
        c2["close"] < c2["open"] and
        c1["close"] > c1["open"]
    )


# ==========================
# 🔥 FILTRO: NO ENTRAR EN RESISTENCIA
# ==========================
def cerca_resistencia(precio, resistencias):

    for r in resistencias:
        if abs(precio - r) < 0.0005:
            return True

    return False


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


def ejecutar_trade(iq, pair):

    status, trade_id = silent(
        iq.buy, MONTO, pair, "call", EXPIRACION
    )

    if not status:
        send_message(f"❌ Entrada rechazada {pair}")
        return

    send_message(f"📊 CALL {pair}\n🔥 Rebote en soporte")

    resultado = obtener_resultado(iq, trade_id)

    if resultado == "win":
        send_message(f"✅ WIN {pair}")
    elif resultado == "draw":
        send_message(f"➖ DRAW {pair}")
    else:
        send_message(f"❌ LOSS {pair}")


def run():

    iq = connect()

    while True:

        esperar_cierre()

        pares = get_otc_abiertos(iq)

        if not pares:
            print("⚠️ No hay OTC abiertos")
            continue

        for par in pares:

            candles = silent(
                iq.get_candles, par, TIMEFRAME, 50, time.time()
            )

            if not candles:
                continue

            soportes, resistencias = detectar_niveles(candles)

            precio_actual = candles[-1]["close"]

            # 🔥 ENVIAR NIVELES A TELEGRAM
            send_message(
                f"📍 {par}\n"
                f"Soportes: {soportes}\n"
                f"Resistencias: {resistencias}"
            )

            # 🔥 FILTRO DE ENTRADA
            if cerca_resistencia(precio_actual, resistencias):
                print(f"🚫 {par} en resistencia")
                continue

            if patron_roja_verde(candles):

                print(f"🎯 {par} rebote detectado")

                esperar_apertura()

                ejecutar_trade(iq, par)

                break
        else:
            print("⚠️ Sin señal...")


if __name__ == "__main__":
    run()
