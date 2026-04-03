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


# 🔔 TELEGRAM SEGURO
def telegram(msg):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        return
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            data={"chat_id": TELEGRAM_CHAT_ID, "text": msg},
            timeout=5
        )
    except Exception as e:
        print(f"⚠️ Telegram error: {e}")


# 🔌 CONEXIÓN ESTABLE
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

            print("❌ Error conexión...")
        except Exception as e:
            print(f"❌ Error conexión: {e}")

        time.sleep(3)


# ⏱️ ESPERA SIGUIENTE VELA
def esperar_siguiente_vela():
    while True:
        now = int(time.time())
        if now % 60 == 0:
            break
        time.sleep(0.2)


# 🚀 EJECUCIÓN REAL ROBUSTA
def ejecutar(iq, accion):

    print(f"⚡ EJECUTANDO: {accion}")
    telegram(f"⚡ EJECUTANDO: {accion}")

    try:
        iq.subscribe_strike_list(PAR, 1)
    except:
        pass

    for intento in range(5):

        try:
            result = iq.buy_digital_spot(PAR, MONTO, accion, EXPIRACION)
        except Exception as e:
            print(f"❌ ERROR API: {e}")
            time.sleep(1)
            continue

        # 🔥 VALIDACIÓN REAL
        if result:
            if isinstance(result, tuple):
                status, order_id = result
            else:
                status, order_id = True, result

            if status:
                print(f"🔥 ORDEN ABIERTA: {order_id}")
                telegram(f"✅ ORDEN EJECUTADA: {accion}")
                return True

        print(f"⚠️ Reintento {intento + 1}")
        time.sleep(1)

    print("❌ FALLÓ TOTAL")
    telegram("❌ NO SE EJECUTÓ")
    return False


# 🔁 LOOP PRINCIPAL
def run():

    iq = conectar()

    try:
        iq.start_candles_stream(PAR, 5, 100)
    except Exception as e:
        print(f"⚠️ Error iniciando velas: {e}")

    while True:

        try:
            señal = detectar_entrada(iq, PAR)

            if señal:
                print(f"📊 SEÑAL DETECTADA: {señal}")
                telegram(f"📊 SEÑAL: {señal}")

                esperar_siguiente_vela()

                ejecutar(iq, señal)

        except Exception as e:
            print(f"❌ ERROR GENERAL: {e}")
            telegram(f"❌ ERROR: {e}")

            # 🔥 RECONEXIÓN AUTOMÁTICA
            iq = conectar()

        time.sleep(0.5)


if __name__ == "__main__":
    run()
