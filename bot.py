import os
import time
import requests
from iqoptionapi.stable_api import IQ_Option
from strategy import detectar_entrada

IQ_EMAIL = os.getenv("IQ_EMAIL")
IQ_PASSWORD = os.getenv("IQ_PASSWORD")

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

PAR = "EURUSD-OTC"
MONTO = 1000
EXPIRACION = 1


def telegram(msg):
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            data={"chat_id": TELEGRAM_CHAT_ID, "text": msg}
        )
    except:
        pass


def conectar():
    while True:
        iq = IQ_Option(IQ_EMAIL, IQ_PASSWORD)
        iq.connect()

        if iq.check_connect():
            iq.change_balance("PRACTICE")
            print("✅ BOT ACTIVADO")
            telegram("🤖 BOT ACTIVADO")
            return iq

        print("❌ Error conexión...")
        time.sleep(3)


def esperar_siguiente_vela():
    while True:
        segundos = time.time() % 60
        if segundos >= 59:
            break
        time.sleep(0.2)


# 🔥 ENTRADA REAL (SOLUCIÓN DEFINITIVA)
def ejecutar(iq, accion):

    print(f"⚡ ENTRANDO: {accion}")
    telegram(f"⚡ ENTRANDO: {accion}")

    for i in range(5):
        try:
            status, id = iq.buy(
                MONTO,
                PAR,
                accion,
                EXPIRACION
            )
        except Exception as e:
            print(f"❌ ERROR: {e}")
            time.sleep(1)
            continue

        if status:
            print(f"🔥 ORDEN ABIERTA: {id}")
            telegram(f"✅ OPERACIÓN ABIERTA: {accion}")
            return True

        print(f"⚠️ Reintento {i+1}")
        time.sleep(1)

    print("❌ NO SE PUDO ENTRAR")
    telegram("❌ FALLÓ ENTRADA")
    return False


def run():

    iq = conectar()

    iq.start_candles_stream(PAR, 5, 100)

    while True:

        try:
            señal = detectar_entrada(iq, PAR)

            if señal:
                print(f"📊 SEÑAL: {señal}")
                telegram(f"📊 SEÑAL: {señal}")

                esperar_siguiente_vela()

                ejecutar(iq, señal)

                time.sleep(60)  # evita duplicar entradas

        except Exception as e:
            print(f"❌ ERROR LOOP: {e}")
            time.sleep(2)


if __name__ == "__main__":
    run()
