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
MONTO = 5000


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


# 🔥 ESPERA SIGUIENTE VELA
def esperar_siguiente_vela():
    while True:
        if int(time.time() % 60) == 0:
            break
        time.sleep(0.2)


# 🔥 EJECUCIÓN DINÁMICA
def ejecutar(iq, accion, expiracion):

    print(f"⚡ ENTRANDO: {accion} | {expiracion} min")
    telegram(f"⚡ ENTRANDO: {accion} | {expiracion} min")

    for i in range(5):
        try:
            status, order_id = iq.buy(
                MONTO,
                PAR,
                accion,
                expiracion
            )
        except Exception as e:
            print(f"❌ ERROR: {e}")
            time.sleep(1)
            continue

        if status:
            print(f"🔥 ORDEN ABIERTA: {order_id}")
            telegram(f"✅ OPERACIÓN: {accion} ({expiracion}m)")
            return True

        print(f"⚠️ Reintento {i+1}")
        time.sleep(1)

    print("❌ FALLÓ ENTRADA")
    telegram("❌ NO SE EJECUTÓ")
    return False


def run():

    iq = conectar()

    iq.start_candles_stream(PAR, 4, 500)

    while True:

        try:
            accion, expiracion = detectar_entrada(iq, PAR)

            if accion:
                print(f"📊 SEÑAL: {accion} | {expiracion}m")
                telegram(f"📊 SEÑAL: {accion} | {expiracion}m")

                esperar_siguiente_vela()

                ejecutar(iq, accion, expiracion)

                time.sleep(60)

        except Exception as e:
            print(f"❌ ERROR LOOP: {e}")
            time.sleep(2)


if __name__ == "__main__":
    run()
