import os
import time
import requests
from iqoptionapi.stable_api import IQ_Option
from strategy import detectar_entrada, actualizar_modelo

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
        try:
            iq = IQ_Option(IQ_EMAIL, IQ_PASSWORD)
            iq.connect()

            if iq.check_connect():
                iq.change_balance("PRACTICE")
                print("✅ BOT IA ACTIVADO")
                telegram("🤖 BOT IA ACTIVADO")
                return iq

        except Exception as e:
            print(f"❌ ERROR CONEXIÓN: {e}")

        time.sleep(3)


def ejecutar(iq, accion):
    print(f"⚡ IA ENTRANDO: {accion}")
    telegram(f"⚡ IA ENTRANDO: {accion}")

    try:
        status, order_id = iq.buy(MONTO, PAR, accion, EXPIRACION)

        if status:
            print(f"🔥 ORDEN ABIERTA: {order_id}")
            return order_id
        else:
            print("❌ ERROR AL EJECUTAR")
            return None

    except Exception as e:
        print(f"❌ ERROR: {e}")
        return None


def verificar_resultado(iq, order_id):
    while True:
        resultado = iq.check_win_v4(order_id)

        if resultado is not None:
            return resultado

        time.sleep(1)


def run():
    iq = conectar()

    ultima_operacion = False

    while True:
        try:
            accion, features = detectar_entrada(iq, PAR)

            if accion and not ultima_operacion:
                order_id = ejecutar(iq, accion)

                if order_id:
                    resultado = verificar_resultado(iq, order_id)

                    print(f"💰 RESULTADO: {resultado}")
                    telegram(f"💰 RESULTADO: {resultado}")

                    # 🔥 IA APRENDE AQUÍ
                    actualizar_modelo(features, resultado)

                ultima_operacion = True
                time.sleep(5)

            if accion is None:
                ultima_operacion = False

            time.sleep(1)

        except Exception as e:
            print(f"❌ ERROR LOOP: {e}")
            time.sleep(3)


if __name__ == "__main__":
    run()
