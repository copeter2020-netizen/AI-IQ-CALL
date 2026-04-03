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
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            data={"chat_id": TELEGRAM_CHAT_ID, "text": msg}
        )
    except:
        pass


# 🔥 CONEXIÓN TOTALMENTE LIMPIA (ELIMINA DIGITAL BUG)
def conectar():
    while True:
        try:
            iq = IQ_Option(IQ_EMAIL, IQ_PASSWORD)
            iq.connect()

            if iq.check_connect():
                iq.change_balance("PRACTICE")

                # 🔥 BLOQUEO TOTAL DE DIGITAL (SOLUCIÓN ERROR underlying)
                try:
                    iq.api.digital_option = None
                    iq.api.get_digital_underlying_list_data = None
                except:
                    pass

                print("✅ BOT ACTIVADO")
                telegram("🤖 BOT ACTIVADO")
                return iq

        except Exception as e:
            print(f"❌ ERROR CONEXIÓN: {e}")

        print("🔁 Reintentando conexión...")
        time.sleep(3)


def activo_abierto(iq, par):
    try:
        data = iq.get_all_open_time()
        return data["binary"][par]["open"]
    except:
        return False


# 🔥 ESPERA NUEVA VELA EXACTA
def esperar_siguiente_vela():
    while True:
        if int(time.time() % 60) == 0:
            break
        time.sleep(0.2)


# 🔥 EJECUCIÓN REAL (SOLO BINARIAS)
def ejecutar(iq, accion, expiracion):

    print(f"⚡ ENTRANDO: {accion} | {expiracion}m")
    telegram(f"⚡ ENTRANDO: {accion} | {expiracion}m")

    for intento in range(5):

        # 🔁 reconexión automática
        if not iq.check_connect():
            print("🔁 Reconectando...")
            iq = conectar()

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
            telegram(f"✅ OPERACIÓN: {accion} ({expiracion}m)")
            return True

        print(f"⚠️ Reintento {intento+1}")
        time.sleep(1)

    print("❌ FALLÓ ENTRADA")
    telegram("❌ NO SE EJECUTÓ")
    return False


def run():

    iq = conectar()

    while True:

        try:
            # 🔒 validar activo abierto
            if not activo_abierto(iq, PAR):
                print("⏳ Activo cerrado...")
                time.sleep(5)
                continue

            accion, expiracion = detectar_entrada(iq, PAR)

            if accion:
                print(f"📊 SEÑAL: {accion} | {expiracion}m")
                telegram(f"📊 SEÑAL: {accion} | {expiracion}m")

                esperar_siguiente_vela()

                ejecutar(iq, accion, expiracion)

                # evita sobreoperar
                time.sleep(60)

        except Exception as e:
            print(f"❌ ERROR LOOP: {e}")
            telegram(f"❌ ERROR: {e}")

            # 🔁 reconexión total
            iq = conectar()

            time.sleep(2)


if __name__ == "__main__":
    run()
