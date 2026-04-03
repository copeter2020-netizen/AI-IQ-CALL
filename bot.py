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
MONTO = 3
EXPIRACION = 1


# =========================
# 📲 TELEGRAM
# =========================
def telegram(msg):
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            data={"chat_id": TELEGRAM_CHAT_ID, "text": msg}
        )
    except:
        pass


# =========================
# 🔌 CONEXIÓN SEGURA
# =========================
def conectar():
    while True:
        try:
            iq = IQ_Option(IQ_EMAIL, IQ_PASSWORD)
            iq.connect()

            if iq.check_connect():
                iq.change_balance("PRACTICE")
                print("✅ BOT CONECTADO")
                telegram("🤖 BOT CONECTADO")
                return iq

        except Exception as e:
            print(f"❌ ERROR CONEXIÓN: {e}")

        time.sleep(3)


# =========================
# 🔥 ESPERAR APERTURA EXACTA
# =========================
def esperar_apertura_vela():
    while True:
        now = time.time()
        segundos = int(now) % 60

        # 🔥 entra EXACTO en segundo 0
        if segundos == 0:
            break

        time.sleep(0.2)


# =========================
# 🚀 EJECUTAR OPERACIÓN
# =========================
def ejecutar(iq, accion):

    print(f"⚡ ENTRANDO: {accion}")
    telegram(f"⚡ ENTRANDO: {accion}")

    for i in range(3):
        try:
            status, order_id = iq.buy(MONTO, PAR, accion, EXPIRACION)

            if status:
                print(f"🔥 ORDEN ABIERTA: {order_id}")
                telegram(f"✅ ORDEN: {accion}")
                return True

        except Exception as e:
            print(f"❌ ERROR ORDEN: {e}")

        time.sleep(1)

    print("❌ NO EJECUTÓ")
    telegram("❌ FALLÓ OPERACIÓN")
    return False


# =========================
# 🧠 LOOP PRINCIPAL
# =========================
def run():

    iq = conectar()

    while True:
        try:
            señal, _ = detectar_entrada(iq, PAR)

            if señal:
                print(f"📊 SEÑAL: {señal}")
                telegram(f"📊 SEÑAL: {señal}")

                # 🔥 ESPERA APERTURA EXACTA
                esperar_apertura_vela()

                # 🔥 EJECUTA EN EL SEGUNDO 0
                ejecutar(iq, señal)

                # 🔒 EVITA MULTIENTRADAS MISMA VELA
                time.sleep(2)

        except Exception as e:
            print(f"❌ ERROR LOOP: {e}")
            time.sleep(2)


# =========================
# ▶️ START
# =========================
if __name__ == "__main__":
    run()
