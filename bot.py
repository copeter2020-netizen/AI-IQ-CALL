import os
import time
from iqoptionapi.stable_api import IQ_Option
from strategy import detectar_entrada

IQ_EMAIL = os.getenv("IQ_EMAIL")
IQ_PASSWORD = os.getenv("IQ_PASSWORD")

PAR = "EURUSD-OTC"  # 🔥 IMPORTANTE
MONTO = 20000
EXPIRACION = 1


def connect():
    while True:
        iq = IQ_Option(IQ_EMAIL, IQ_PASSWORD)
        iq.connect()

        if iq.check_connect():
            iq.change_balance("PRACTICE")
            print("✅ BOT ACTIVADO")
            return iq

        print("❌ Error conectando...")
        time.sleep(3)


# 🔥 SNIPER EXACTO
def esperar_sniper():
    while int(time.time()) % 60 != 59:
        time.sleep(0.001)


# 🔥 EJECUCIÓN DIGITAL REAL (SIN ERROR)
def ejecutar(iq, accion):

    print(f"⚡ ENTRANDO: {accion}")

    try:
        id = iq.buy_digital_spot(PAR, MONTO, accion, EXPIRACION)
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return

    if id:
        print(f"🔥 ENTRADA EJECUTADA ID: {id}")
    else:
        print("❌ FALLÓ LA ORDEN")


def run():

    iq = connect()

    while True:

        try:
            señal = detectar_entrada(iq, PAR)

            if señal:
                print(f"📊 SEÑAL: {señal}")

                esperar_sniper()
                ejecutar(iq, señal)

        except Exception as e:
            print(f"❌ ERROR GENERAL: {e}")
            iq = connect()

        time.sleep(0.5)


if __name__ == "__main__":
    run()
