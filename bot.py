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
MONTO = 20000
EXPIRACION = 1


def telegram(msg):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": msg})
    except:
        pass


def connect():
    while True:
        iq = IQ_Option(IQ_EMAIL, IQ_PASSWORD)
        iq.connect()

        if iq.check_connect():
            iq.change_balance("PRACTICE")
            print("✅ BOT ACTIVADO")
            telegram("🤖 BOT ACTIVADO")
            return iq

        print("❌ Error conectando...")
        time.sleep(3)


# 🔥 SNIPER 1 SEG ANTES
def esperar_sniper():
    while int(time.time()) % 60 != 59:
        time.sleep(0.001)


# 🔥 ENTRADA REAL CON REINTENTO
def ejecutar(iq, accion):

    print(f"⚡ ENTRANDO: {accion}")
    telegram(f"📊 ENTRANDO: {accion}")

    # 🔥 SUSCRIPCIÓN (CLAVE)
    iq.subscribe_strike_list(PAR, 1)

    for intento in range(3):

        try:
            id = iq.buy_digital_spot(PAR, MONTO, accion, EXPIRACION)
        except Exception as e:
            print(f"❌ ERROR: {e}")
            continue

        if id:
            print(f"🔥 ORDEN ABIERTA: {id}")
            telegram(f"✅ ORDEN EJECUTADA: {accion}")
            return True

        print(f"⚠️ Reintentando... {intento+1}")
        time.sleep(1)

    print("❌ NO SE PUDO EJECUTAR")
    telegram("❌ ERROR: NO EJECUTÓ")
    return False


def run():

    iq = connect()

    # 🔥 ACTIVA STREAM (IMPORTANTE)
    iq.start_candles_stream(PAR, 5, 100)

    while True:

        try:
            señal = detectar_entrada(iq, PAR)

            if señal:
                print(f"📊 SEÑAL: {señal}")
                telegram(f"📊 SEÑAL: {señal}")

                esperar_sniper()
                ejecutar(iq, señal)

        except Exception as e:
            print(f"❌ ERROR GENERAL: {e}")
            telegram(f"❌ ERROR: {e}")
            iq = connect()

        time.sleep(0.5)


if __name__ == "__main__":
    run()
