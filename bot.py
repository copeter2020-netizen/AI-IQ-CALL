import time
import os
import requests
from iqoptionapi.stable_api import IQ_Option
from estrategia import detectar_entrada_oculta

EMAIL = os.getenv("IQ_EMAIL")
PASSWORD = os.getenv("IQ_PASSWORD")
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

MONTO = 3333
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
# DATOS
# =========================
def obtener_velas(iq):
    try:
        return iq.get_candles("EURUSD-OTC", 60, 30, time.time())
    except:
        return None


def obtener_precio(iq):
    try:
        return iq.get_candles("EURUSD-OTC", 1, 1, time.time())[0]["close"]
    except:
        return None


# =========================
# TIEMPO
# =========================
def esperar_cierre():
    while int(time.time() % 60) != 59:
        time.sleep(0.1)


def esperar_nueva_vela():
    while int(time.time() % 60) > 1:
        time.sleep(0.05)


# =========================
# ENTRADA SNIPER
# =========================
def entrada_sniper(iq, direccion, apertura):
    log("🎯 Buscando entrada sniper...")

    tocado = False
    rechazo = False

    inicio = time.time()

    while True:
        segundos = int(time.time() % 60)

        # 🔥 SOLO PRIMEROS 30 SEGUNDOS
        if segundos > 30:
            log("❌ No hubo entrada sniper")
            return False

        precio = obtener_precio(iq)

        if not precio:
            continue

        # =========================
        # FASE 1: TOQUE
        # =========================
        if not tocado:
            if direccion == "call" and precio < apertura:
                tocado = True

            if direccion == "put" and precio > apertura:
                tocado = True

        # =========================
        # FASE 2: RECHAZO
        # =========================
        if tocado and not rechazo:
            if direccion == "call" and precio > apertura:
                rechazo = True

            if direccion == "put" and precio < apertura:
                rechazo = True

        # =========================
        # FASE 3: CONFIRMACIÓN
        # =========================
        if tocado and rechazo:
            log("🚀 Entrada sniper confirmada")

            for _ in range(3):
                try:
                    status, order_id = iq.buy(MONTO, "EURUSD-OTC", direccion, 1)

                    if status:
                        log(f"""🔥 OPERACIÓN SNIPER

EURUSD-OTC {direccion.upper()}
ID: {order_id}
""")
                        return True
                except:
                    pass

                time.sleep(1)

            log("❌ Falló ejecución")
            return False

        time.sleep(0.1)


# =========================
# MAIN
# =========================
def run():
    global ultima_entrada

    iq = conectar()

    while True:
        try:
            iq = asegurar_conexion(iq)

            # 🔥 ESPERAR CIERRE
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
📊 SEÑAL SNIPER

EURUSD-OTC {direccion}
""")

            # 🔥 NUEVA VELA
            esperar_nueva_vela()

            nueva_vela = obtener_velas(iq)

            if not nueva_vela:
                continue

            apertura = nueva_vela[-1]["open"]

            # 🔥 ENTRADA AVANZADA
            if entrada_sniper(iq, direccion, apertura):
                ultima_entrada = time.time()

        except Exception as e:
            log(f"Error: {e}")
            time.sleep(2)


if __name__ == "__main__":
    run()
