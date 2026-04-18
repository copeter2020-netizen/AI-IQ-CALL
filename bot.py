import time
import os
from iqoptionapi.stable_api import IQ_Option
from estrategia import detectar_entrada_oculta

EMAIL = os.getenv("IQ_EMAIL")
PASSWORD = os.getenv("IQ_PASSWORD")

MONTO = 1000
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

        except Exception as e:
            print("Error conexión:", e)

        time.sleep(5)


def obtener_velas(iq, par):
    try:
        return iq.get_candles(par, 60, 50, time.time())
    except Exception as e:
        print("Error velas:", e)
        return None


def operar(iq, par, direccion):
    global ultima_entrada

    if time.time() - ultima_entrada < 10:
        return

    for intento in range(3):
        try:
            status, order_id = iq.buy(MONTO, par, direccion, 1)

            if status:
                print(f"🚀 {par} {direccion} | ID: {order_id}")
                ultima_entrada = time.time()
                return
            else:
                print("⚠️ Reintentando...")

        except Exception as e:
            print("Error operación:", e)

        time.sleep(1)

    print("❌ Falló ejecución")


def run():
    iq = conectar()

    PAR = "EURUSD-OTC"

    while True:
        try:
            velas = obtener_velas(iq, PAR)

            if not velas:
                time.sleep(1)
                continue

            data = {PAR: velas}

            señal = detectar_entrada_oculta(data)

            if señal:
                par, direccion, score = señal

                print(f"""
📈 SEÑAL
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
