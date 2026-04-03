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
MONTO = 1
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


# 🔥 ESPERA SIGUIENTE VELA REAL (NO SNIPER)
def esperar_siguiente_vela():
    actual = int(time.time())
    restante = 60 - (actual % 60)
    time.sleep(restante + 0.2)


# 🔥 EJECUCIÓN REAL
def ejecutar(iq, accion):

    print(f"⚡ EJECUTANDO: {accion}")
    telegram(f"⚡ EJECUTANDO: {accion}")

    iq.subscribe_strike_list(PAR, 1)

    for i in range(5):
        try:
            status, id = iq.buy_digital_spot(PAR, MONTO, accion, EXPIRACION)
        except Exception as e:
            print(f"❌ ERROR API: {e}")
            continue

        if status:
            print(f"🔥 ORDEN ABIERTA: {id}")
            telegram(f"✅ ORDEN EJECUTADA: {accion}")
            return True

        print(f"⚠️ Reintento {i+1}")
        time.sleep(1)

    print("❌ FALLÓ TOTAL")
    telegram("❌ NO SE EJECUTÓ")
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

                # 🔥 ESPERA LA SIGUIENTE VELA
                esperar_siguiente_vela()

                ejecutar(iq, señal)

        except Exception as
