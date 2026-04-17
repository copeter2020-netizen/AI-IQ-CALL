import time
import os
from iqoptionapi.stable_api import IQ_Option
from estrategia import detectar_entrada_oculta

EMAIL = os.getenv("IQ_EMAIL")
PASSWORD = os.getenv("IQ_PASSWORD")

MONTO = 540
CUENTA = "PRACTICE"

ultima_entrada = 0


def conectar():
    while True:
        iq = IQ_Option(EMAIL, PASSWORD)
        iq.connect()

        if iq.check_connect():
            iq.change_balance(CUENTA)
            print("✅ BOT CONECTADO")
            return iq

        time.sleep(5)


def activo_abierto(iq, par):
    try:
        return iq.get_all_open_time()["digital"][par]["open"]
    except:
        return False


def obtener_velas(iq, par, tf):
    try:
        return iq.get_candles(par, tf, 50, time.time())
    except:
        return None


def operar(iq, par, direccion):
    global ultima_entrada

    if time.time() - ultima_entrada < 5:
        return

    if not activo_abierto(iq, par):
        print(f"❌ {par} cerrado")
        return

    for intento in range(3):  # 🔥 reintentos reales
        try:
            iq.subscribe_strike_list(par, 1)
            time.sleep(0.3)

            status, order_id = iq.buy_digital_spot(par, MONTO, direccion, 1)

            iq.unsubscribe_strike_list(par, 1)

            if status:
                print(f"🚀 {par} {direccion} ID:{order_id}")
                ultima_entrada = time.time()
                return
            else:
                print("⚠️ Reintentando...")

        except Exception as e:
            print("Error:", e)

    print("❌ Falló totalmente la ejecución")


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

                print(f"\n📈 SEÑAL\n{par} {direccion}\nScore: {score}")

                operar(iq, par, direccion)

            time.sleep(0.5)

        except Exception as e:
            print("Error general:", e)
            time.sleep(2)


if __name__ == "__main__":
    run()
