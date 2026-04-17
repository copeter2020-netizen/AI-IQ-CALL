import time
import os
import requests
from iqoptionapi.stable_api import IQ_Option
from estrategia import detectar_entrada_oculta

EMAIL = os.getenv("IQ_EMAIL")
PASSWORD = os.getenv("IQ_PASSWORD")

MONTO = 508
CUENTA = "PRACTICE"

ultima_entrada = 0


def conectar():
    while True:
        try:
            iq = IQ_Option(EMAIL, PASSWORD)
            iq.connect()

            if iq.check_connect():
                iq.change_balance(CUENTA)
                print("✅ BOT CONECTADO")
                return iq
        except:
            pass
        time.sleep(5)


def obtener_velas(iq, par, timeframe):
    try:
        return iq.get_candles(par, timeframe, 50, time.time())
    except:
        return None


def operar(iq, par, direccion):
    global ultima_entrada

    if time.time() - ultima_entrada < 10:
        return

    try:
        status, _ = iq.buy(MONTO, par, direccion, 1)

        if status:
            print(f"🚀 {par} {direccion}")
            ultima_entrada = time.time()
        else:
            print("❌ No ejecutó")

    except Exception as e:
        print("Error:", e)


def run():
    iq = conectar()

    PARES = [
        "EURUSD-OTC",
        "GBPUSD-OTC",
        "USDJPY-OTC",
        "USDCHF-OTC",
        "EURJPY-OTC",
        "GBPJPY-OTC"
    ]

    while True:
        try:
            data = {}

            for par in PARES:

                m1 = obtener_velas(iq, par, 60)
                m5 = obtener_velas(iq, par, 300)

                if m1 and m5:
                    data[par] = {"m1": m1, "m5": m5}

            señal = detectar_entrada_oculta(data)

            if señal:
                par, direccion, score = señal

                print(f"""
📊 SEÑAL
{par} {direccion}
Score: {score}
""")

                operar(iq, par, direccion)

            time.sleep(0.5)

        except Exception as e:
            print("Error general:", e)
            time.sleep(2)


if __name__ == "__main__":
    run()
