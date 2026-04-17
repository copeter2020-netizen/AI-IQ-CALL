import time
import os
import requests
from iqoptionapi.stable_api import IQ_Option
from estrategia import detectar_entrada_oculta

EMAIL = os.getenv("IQ_EMAIL")
PASSWORD = os.getenv("IQ_PASSWORD")
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

MONTO = 565
CUENTA = "PRACTICE"

ultima_entrada = 0
ultimo_par = None


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
# VELAS
# =========================
def obtener_velas(iq, par, tf):
    try:
        return iq.get_candles(par, tf, 50, time.time())
    except:
        return None


# =========================
# OPERAR
# =========================
def operar(iq, par, direccion):
    global ultima_entrada, ultimo_par

    if time.time() - ultima_entrada < 30:
        return

    if par == ultimo_par:
        return

    log(f"⏳ Esperando entrada {par}")

    esperar_cierre()

    for i in range(3):
        try:
            status, order_id = iq.buy(MONTO, par, direccion, 1)

            if status:
                log(f"""🚀 OPERACIÓN

{par} {direccion.upper()}
ID: {order_id}
""")
                ultima_entrada = time.time()
                ultimo_par = par
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

            señal = detectar_entrada_oculta(data)

            if señal:
                par, direccion, score = señal

                if score < 7:
                    continue

                log(f"""
📈 MOMENTUM DETECTADO
{par} {direccion}
Score: {score}
""")

                operar(iq, par, direccion)

            time.sleep(0.5)

        except Exception as e:
            log(f"Error: {e}")
            time.sleep(2)


if __name__ == "__main__":
    run() 
