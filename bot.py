import time
import os
import requests
from iqoptionapi.stable_api import IQ_Option
from estrategia import detectar_entrada_oculta

EMAIL = os.getenv("IQ_EMAIL")
PASSWORD = os.getenv("IQ_PASSWORD")
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

MONTO = 2000
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
# PRECIO ACTUAL
# =========================
def obtener_precio(iq):
    try:
        return iq.get_candles("EURUSD-OTC", 1, 1, time.time())[0]["close"]
    except:
        return None


# =========================
# ESPERAR RETROCESO
# =========================
def esperar_retroceso(iq, direccion, apertura):
    inicio = time.time()

    while time.time() - inicio < 20:  # máximo 20s esperando
        precio = obtener_precio(iq)

        if not precio:
            continue

        # 🔥 lógica clave
        if direccion == "call" and precio < apertura:
            return True

        if direccion == "put" and precio > apertura:
            return True

        time.sleep(0.2)

    return False


# =========================
# OPERAR
# =========================
def operar(iq, direccion, apertura):
    global ultima_entrada

    if time.time() - ultima_entrada < 30:
        return

    log("⏳ Esperando retroceso a la apertura...")

    retroceso = esperar_retroceso(iq, direccion, apertura)

    if not retroceso:
        log("❌ No hubo retroceso válido")
        return

    try:
        status, order_id = iq.buy(MONTO, "EURUSD-OTC", direccion, 1)

        if status:
            log(f"""🚀 OPERACIÓN (RETROCESO)

EURUSD-OTC {direccion.upper()}
ID: {order_id}
""")
            ultima_entrada = time.time()
        else:
            log("❌ No ejecutó")

    except Exception as e:
        log(f"Error operación: {e}")


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
                time.sleep(0.5)
                continue

            velas_parseadas = [{
                "open": v["open"],
                "close": v["close"],
                "max": v["max"],
                "min": v["min"]
            } for v in velas]

            data = {"EURUSD-OTC": velas_parseadas}

            señal = detectar_entrada_oculta(data)

            if señal:
                par, direccion, score = señal

                vela_actual = velas_parseadas[-1]
                apertura = vela_actual["open"]

                log(f"""
📈 SEÑAL CON RETROCESO

EURUSD-OTC {direccion}
Esperando entrada bajo apertura
""")

                operar(iq, direccion, apertura)

            time.sleep(0.2)

        except Exception as e:
            log(f"Error: {e}")
            time.sleep(2)


if __name__ == "__main__":
    run()
