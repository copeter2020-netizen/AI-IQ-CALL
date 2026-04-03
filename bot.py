import os
import time
from iqoptionapi.stable_api import IQ_Option
from strategy import detectar_entrada

IQ_EMAIL = os.getenv("IQ_EMAIL")
IQ_PASSWORD = os.getenv("IQ_PASSWORD")

PAR = "EURUSD"
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


# 🔥 SNIPER REAL (SIN DESFASE)
def esperar_sniper():
    while True:
        now = time.time()
        segundos = int(now) % 60

        if segundos == 59:
            break

        time.sleep(0.001)


# 🔥 EJECUCIÓN REAL FORZADA
def ejecutar(iq, accion):

    print(f"⚡ INTENTANDO ENTRADA: {accion}")

    try:
        status, id = iq.buy(MONTO, PAR, accion, EXPIRACION)
    except Exception as e:
        print(f"❌ ERROR BUY: {e}")
        return

    if status:
        print(f"🔥 ENTRADA EJECUTADA: {accion.upper()} ID: {id}")
    else:
        print("❌ FALLÓ LA ENTRADA")


def run():

    iq = connect()

    while True:

        try:
            señal = detectar_entrada(iq, PAR)

            if señal:

                print(f"📊 SEÑAL DETECTADA: {señal}")

                esperar_sniper()
                ejecutar(iq, señal)

        except Exception as e:
            print(f"❌ ERROR GENERAL: {e}")
            iq = connect()

        time.sleep(0.5)


if __name__ == "__main__":
    run()
