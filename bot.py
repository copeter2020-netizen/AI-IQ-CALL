import time
import os
import requests
from iqoptionapi.stable_api import IQ_Option
from estrategia import detectar_entrada_oculta

EMAIL = os.getenv("IQ_EMAIL")
PASSWORD = os.getenv("IQ_PASSWORD")
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

MONTO = 500
CUENTA = "PRACTICE"

ultima_entrada = 0


# =========================
# TELEGRAM
# =========================
def enviar_telegram(msg):
    try:
        requests.post(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            data={"chat_id": CHAT_ID, "text": msg},
            timeout=5
        )
    except:
        pass


def log(msg):
    print(msg, flush=True)
    enviar_telegram(msg)


# =========================
# CONEXIÓN
# =========================
def conectar():
    while True:
        try:
            iq = IQ_Option(EMAIL, PASSWORD)
            iq.connect()

            if iq.check_connect():
                iq.change_balance(CUENTA)

                try:
                    iq.api.digital_option = None
                except:
                    pass

                log("✅ BOT CONECTADO")
                return iq

        except Exception as e:
            log(f"Error conexión: {e}")

        time.sleep(5)


def asegurar_conexion(iq):
    try:
        if not iq.check_connect():
            return conectar()
        return iq
    except:
        return conectar()


# =========================
# TIMING
# =========================
def esperar_cierre():
    while int(time.time() % 60) < 59:
        time.sleep(0.01)


# =========================
# VELAS M1
# =========================
def obtener_velas(iq):
    try:
        return iq.get_candles("EURUSD-OTC", 60, 30, time.time())
    except:
        return None


# =========================
# OPERAR
# =========================
def operar(iq, direccion):
    global ultima_entrada

    if time.time() - ultima_entrada < 30:
        return

    log("⏳ Esperando cierre M1...")

    esperar_cierre()

    for i in range(3):
        try:
            status, order_id = iq.buy(MONTO, "EURUSD-OTC", direccion, 1)

            if status:
                log(f"""🚀 OPERACIÓN

EURUSD-OTC {direccion.upper()}
ID: {order_id}
""")
                ultima_entrada = time.time()
                return
        except:
            pass

        time.sleep(1)

    log("❌ No ejecutó")


# =========================
# MAIN
# =========================
def run():
    iq = conectar()

    while True:
        try:
            iq = asegurar_conexion(iq)

            velas = obtener_velas(iq)

            if not velas:
                time.sleep(1)
                continue

            data = {
                "EURUSD-OTC": [{
                    "open": v["open"],
                    "close": v["close"],
                    "max": v["max"],
                    "min": v["min"]
                } for v in velas]
            }

            señal = detectar_entrada_oculta(data)

            if señal:
                par, direccion, score = señal

                log(f"""
📈 MOMENTUM PURO
EURUSD-OTC {direccion}
""")

                operar(iq, direccion)

            time.sleep(0.3)

        except Exception as e:
            log(f"Error: {e}")
            time.sleep(2)


if __name__ == "__main__":
    run()
