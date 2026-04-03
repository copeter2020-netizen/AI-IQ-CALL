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


def telegram(msg):
    try:
        if TELEGRAM_TOKEN and TELEGRAM_CHAT_ID:
            requests.post(
                f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
                data={"chat_id": TELEGRAM_CHAT_ID, "text": msg}
            )
    except:
        pass


# 🔥 PARCHE GLOBAL ANTI-DIGITAL (ELIMINA 'underlying')
def parche_anti_digital(iq):
    try:
        iq.get_digital_underlying_list_data = lambda: {"underlying": []}
    except:
        pass


def conectar():
    while True:
        try:
            iq = IQ_Option(IQ_EMAIL, IQ_PASSWORD)
            iq.connect()

            if iq.check_connect():
                iq.change_balance("PRACTICE")

                # 🔥 aplicar parche después de conectar
                parche_anti_digital(iq)

                print("✅ BOT ACTIVADO")
                telegram("🤖 BOT ACTIVADO")

                return iq

        except Exception as e:
            print(f"❌ ERROR CONEXIÓN: {e}")

        time.sleep(3)


def activo_abierto(iq, par):
    try:
        data = iq.get_all_open_time()
        return data["binary"][par]["open"]
    except:
        return False


# ⏱️ sincroniza entrada a nueva vela
def esperar_siguiente_vela():
    while True:
        if int(time.time()) % 60 == 0:
            break
        time.sleep(0.2)


# 🔥 EJECUCIÓN BINARIA (SIN DIGITAL)
def ejecutar(iq, accion, expiracion):

    print(f"⚡ ENTRANDO: {accion}")
    telegram(f"⚡ ENTRANDO: {accion}")

    for _ in range(5):
        try:
            status, order_id = iq.buy(
                MONTO,
                PAR,
                accion,
                expiracion
            )
        except Exception as e:
            print(f"❌ ERROR API: {e}")
            time.sleep(1)
            continue

        if status:
            print(f"🔥 ORDEN ABIERTA: {order_id}")
            telegram(f"✅ OPERACIÓN {accion}")
            return True

        time.sleep(1)

    print("❌ FALLÓ ENTRADA")
    telegram("❌ NO SE EJECUTÓ")
    return False


def run():

    iq = conectar()

    while True:
        try:

            if not activo_abierto(iq, PAR):
                print("⏳ Mercado cerrado")
                time.sleep(5)
                continue

            accion, expiracion = detectar_entrada(iq, PAR)

            if accion:
                print(f"📊 SEÑAL: {accion}")
                telegram(f"📊 SEÑAL: {accion}")

                esperar_siguiente_vela()

                ejecutar(iq, accion, expiracion)

                time.sleep(60)

        except Exception as e:
            print(f"❌ ERROR LOOP: {e}")
            telegram(f"❌ ERROR: {e}")
            iq = conectar()


if __name__ == "__main__":
    run()
