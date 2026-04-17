import time
import os
import requests
from iqoptionapi.stable_api import IQ_Option
from estrategia import detectar_entrada_oculta

EMAIL = os.getenv("IQ_EMAIL")
PASSWORD = os.getenv("IQ_PASSWORD")
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

MONTO = 560
CUENTA = "PRACTICE"

ultima_entrada = 0


# =========================
# TELEGRAM + LOG
# =========================
def enviar_telegram(msg):
    if not TOKEN or not CHAT_ID:
        return
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

                # 🔥 DESACTIVA DIGITAL (CLAVE)
                try:
                    iq.api.digital_option = None
                except:
                    pass

                log("✅ BOT CONECTADO")
                return iq

        except Exception as e:
            log(f"❌ Error conexión: {e}")

        time.sleep(5)


def asegurar_conexion(iq):
    try:
        if not iq.check_connect():
            log("🔄 Reconectando...")
            return conectar()
        return iq
    except:
        return conectar()


# =========================
# VALIDAR ACTIVO
# =========================
def activo_abierto(iq, par):
    try:
        data = iq.get_all_open_time()
        return data["binary"].get(par, {}).get("open", True)
    except:
        return True


# =========================
# TIMING PRECISO
# =========================
def esperar_cierre():
    while True:
        if int(time.time() % 60) >= 59:
            break
        time.sleep(0.01)


# =========================
# VELAS
# =========================
def obtener_velas(iq, par, timeframe):
    try:
        return iq.get_candles(par, timeframe, 50, time.time())
    except:
        return None


# =========================
# OPERAR (ULTRA ESTABLE)
# =========================
def operar(iq, par, direccion):
    global ultima_entrada

    if time.time() - ultima_entrada < 10:
        return

    if not activo_abierto(iq, par):
        log(f"❌ {par} cerrado")
        return

    log(f"⏳ Esperando cierre {par}...")

    esperar_cierre()

    # 🔥 ejecutar varias veces hasta que entre
    for intento in range(5):
        try:
            status, order_id = iq.buy(MONTO, par, direccion, 1)

            if status:
                log(f"""🚀 OPERACIÓN EJECUTADA

Par: {par}
Dirección: {direccion.upper()}
Monto: {MONTO}
ID: {order_id}
""")
                ultima_entrada = time.time()
                return

            else:
                log(f"⚠️ Reintentando ({intento+1}/5)...")

        except Exception as e:
            # 🔥 IGNORA ERROR UNDERLYING
            if "underlying" in str(e):
                continue

            log(f"⚠️ Error intento: {e}")

        time.sleep(1)

    log("❌ Falló ejecución total")


# =========================
# MAIN
# =========================
def run():
    iq = conectar()

    PARES = [
        "EURUSD-OTC",
        "GBPUSD-OTC",
        "USDZAR-OTC",
        "USDCHF-OTC",
        "EURJPY-OTC",
        "GBPJPY-OTC"
    ]

    while True:
        try:
            iq = asegurar_conexion(iq)

            data = {}

            for par in PARES:
                m1 = obtener_velas(iq, par, 60)
                m5 = obtener_velas(iq, par, 300)

                if m1 and m5:
                    data[par] = {"m1": m1, "m5": m5}

            if not data:
                time.sleep(1)
                continue

            señal = detectar_entrada_oculta(data)

            if señal:
                par, direccion, score = señal

                log(f"""📈 SEÑAL DETECTADA

{par} {direccion}
Score: {score}
""")

                operar(iq, par, direccion)

            time.sleep(0.5)

        except Exception as e:
            log(f"❌ Error general: {e}")
            time.sleep(2)


if __name__ == "__main__":
    run()
