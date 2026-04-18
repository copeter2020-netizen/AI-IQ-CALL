import time
import os
import requests
from iqoptionapi.stable_api import IQ_Option
from estrategia import detectar_entrada_oculta

EMAIL = os.getenv("IQ_EMAIL")
PASSWORD = os.getenv("IQ_PASSWORD")
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

MONTO = 1
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


def esperar_inicio_siguiente_vela():
    while int(time.time() % 60) != 0:
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

            # 🔥 1. detectar señal
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
Esperando 3 velas...
""")

            # 🔥 vela 1
            esperar_cierre()
            log("🕯 Vela 1 completada")

            # 🔥 vela 2
            esperar_cierre()
            log("🕯 Vela 2 completada")

            # 🔥 vela 3
            esperar_cierre()
            log("🕯 Vela 3 completada")

            # 🔥 entrada en vela 4
            log("🎯 Ejecutando entrada en 4ta vela")

            esperar_inicio_siguiente_vela()

            # 🔥 SIN INVERSIÓN (DIRECTO)
            log(f"📌 Dirección: {direccion.upper()}")

            operar(iq, direccion)

        except Exception as e:
            log(f"Error: {e}")
            time.sleep(2)


if __name__ == "__main__":
    run()
