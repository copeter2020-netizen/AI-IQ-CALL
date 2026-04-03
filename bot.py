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
MONTO = 1200


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
        try:
            iq = IQ_Option(IQ_EMAIL, IQ_PASSWORD)
            iq.connect()

            if iq.check_connect():
                iq.change_balance("PRACTICE")
                print("✅ BOT ACTIVADO")
                telegram("🤖 BOT ACTIVADO")
                return iq

        except Exception as e:
            print(f"❌ ERROR CONEXIÓN: {e}")

        time.sleep(1)


def ejecutar(iq, accion, expiracion):
    print(f"⚡ ENTRANDO: {accion} ({expiracion}m)")
    telegram(f"⚡ ENTRANDO: {accion} ({expiracion}m)")

    try:
        status, order_id = iq.buy(MONTO, PAR, accion, expiracion)

        if status:
            print(f"🔥 ORDEN ABIERTA: {order_id}")
            telegram(f"🔥 ORDEN ABIERTA: {accion}")
            return True
        else:
            print("❌ ERROR AL EJECUTAR")
            telegram("❌ ERROR AL EJECUTAR")
            return False

    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False


def run():
    iq = conectar()

    while True:
        try:
            accion, expiracion = detectar_entrada(iq, PAR)

            if accion:
                print(f"📊 SEÑAL: {accion}")
                telegram(f"📊 SEÑAL: {accion}")

                # 🔥 ENTRADA INMEDIATA (LO QUE PEDISTE)
                ejecutar(iq, accion, expiracion)

                # evitar sobreoperar
                time.sleep(5)

            time.sleep(1)

        except Exception as e:
            print(f"❌ ERROR LOOP: {e}")
            time.sleep(3)


if __name__ == "__main__":
    run()
