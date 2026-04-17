import time
import os
import requests
from iqoptionapi.stable_api import IQ_Option
from estrategia import detectar_entrada_oculta

EMAIL = os.getenv("IQ_EMAIL")
PASSWORD = os.getenv("IQ_PASSWORD")
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

MONTO = 1000
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
# VELAS
# =========================
def obtener_velas(iq):
    try:
        return iq.get_candles("EURUSD-OTC", 60, 30, time.time())
    except:
        return None


# =========================
# TIEMPO
# =========================
def esperar_cierre():
    while int(time.time() % 60) != 59:
        time.sleep(0.1)


def esperar_inicio_vela():
    while int(time.time() % 60) > 1:
        time.sleep(0.05)


# =========================
# OPERAR
# =========================
def operar(iq, direccion):
    global ultima_entrada

    if time.time() - ultima_entrada < 60:
        return

    for _ in range(3):
        try:
            status, order_id = iq.buy(MONTO, "EURUSD-OTC", direccion, 1)

            if status:
                log(f"""🚀 OPERACIÓN EJECUTADA

EURUSD-OTC {direccion.upper()}
ID: {order_id}
""")
                ultima_entrada = time.time()
                return
        except:
            pass

        time.sleep(1)

    log("❌ Falló ejecución")


# =========================
# MAIN
# =========================
def run():
    iq = conectar()

    while True:
        try:
            iq = asegurar_conexion(iq)

            # 🔥 1. ESPERAR CIERRE (VELA SEÑAL)
            esperar_cierre()

            velas = obtener_velas(iq)

            if not velas:
                continue

            velas_parseadas = [{
                "open": v["open"],
                "close": v["close"],
                "max": v["max"],
                "min": v["min"]
            } for v in velas]

            data = {"EURUSD-OTC": velas_parseadas}

            señal = detectar_entrada_oculta(data)

            if not señal:
                continue

            par, direccion, score = señal

            log(f"""
📊 SEÑAL DETECTADA

EURUSD-OTC {direccion}
Esperando confirmación...
""")

            # 🔥 2. ESPERAR 1 VELA COMPLETA (confirmación)
            esperar_cierre()

            log("⏳ Vela de confirmación completada")

            # 🔥 3. ESPERAR INICIO DE LA SIGUIENTE (vela de entrada)
            esperar_inicio_vela()

            log("🎯 Ejecutando entrada en nueva vela")

            # 🔥 4. ENTRAR
            operar(iq, direccion)

        except Exception as e:
            log(f"Error: {e}")
            time.sleep(2)


if __name__ == "__main__":
    run()
