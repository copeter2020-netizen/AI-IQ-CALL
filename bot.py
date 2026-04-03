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
MONTO = 10000
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


# 🔥 ESPERA EXACTA A LA SIGUIENTE VELA
def esperar_siguiente_vela():
    while True:
        segundos = int(time.time() % 60)

        # entra justo cuando empieza la nueva vela
        if segundos == 0:
            break

        time.sleep(0.2)


# 🔥 EJECUCIÓN REAL
def ejecutar(iq, accion):

    print(f"⚡ ENTRANDO: {accion}")
    telegram(f"⚡ ENTRANDO: {accion}")

    for intento in range(5):
        try:
            status, order_id = iq.buy(
                MONTO,
                PAR,
                accion,
                EXPIRACION
            )
        except Exception as e:
            print(f"❌ ERROR API: {e}")
            time.sleep(1)
            continue

        if status:
            print(f"🔥 ORDEN ABIERTA: {order_id}")
            telegram(f"✅ OPERACIÓN ABIERTA: {accion}")
            return True

        print(f"⚠️ Reintento {intento+1}")
        time.sleep(1)

    print("❌ NO SE EJECUTÓ")
    telegram("❌ FALLÓ ENTRADA")
    return False


def run():

    iq = conectar()

    iq.start_candles_stream(PAR, 5, 100)

    while True:

        try:
            señal = detectar_entrada(iq, PAR)

            if señal:
                print(f"📊 SEÑAL DETECTADA: {señal}")
                telegram(f"📊 SEÑAL: {señal}")

                # 🔥 ENTRA EN LA SIGUIENTE VELA
                esperar_siguiente_vela()

                ejecutar(iq, señal)

                # evita duplicar entradas
                time.sleep(60)

        except Exception as e:
            print(f"❌ ERROR LOOP: {e}")
            time.sleep(2)


if __name__ == "__main__":
    run()
