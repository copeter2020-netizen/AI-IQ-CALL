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

ultima_entrada = 0


# =========================
# TELEGRAM (SIN ERRORES)
# =========================
def enviar_telegram(msg):
    try:
        requests.post(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            data={"chat_id": CHAT_ID, "text": msg},
            timeout=10
        )
    except:
        pass  # 🔥 elimina spam error


def log(msg):
    print(msg)
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
                iq.change_balance("PRACTICE")

                print("✅ BOT CONECTADO")
                return iq

        except Exception as e:
            print("Error conexión:", e)

        time.sleep(5)


# =========================
# VELAS
# =========================
def obtener_velas(iq, par):
    try:
        velas = iq.get_candles(par, 60, 30, time.time())

        if not velas:
            return None

        return [{
            "open": v["open"],
            "close": v["close"],
            "max": v["max"],
            "min": v["min"]
        } for v in velas]

    except:
        return None


# =========================
# OPERAR (INMEDIATO)
# =========================
def operar(iq, par, direccion):
    global ultima_entrada

    if time.time() - ultima_entrada < 20:
        return

    try:
        status, _ = iq.buy_digital_spot(par, MONTO, direccion, 1)

        if status:
            log(f"""
🚀 OPERACIÓN EJECUTADA
{par} {direccion.upper()}
""")
            ultima_entrada = time.time()
        else:
            print("❌ No ejecutó")

    except Exception as e:
        print("Error operación:", e)


# =========================
# PARES OTC REALES (SIN ERROR)
# =========================
PARES = [
    "EURUSD-OTC",
    "GBPUSD-OTC",
    "USDCHF-OTC",
    "EURJPY-OTC",
    "GBPJPY-OTC",
    "EURGBP-OTC"
]


# =========================
# MAIN
# =========================
def run():
    iq = conectar()

    while True:
        try:
            data = {}

            for par in PARES:
                velas = obtener_velas(iq, par)
                if velas:
                    data[par] = velas

            if not data:
                time.sleep(1)
                continue

            señal = detectar_entrada_oculta(data)

            if señal:
                par, direccion, score = señal

                log(f"""
🎯 SEÑAL DETECTADA
{par} {direccion}
Score: {score}
""")

                operar(iq, par, direccion)

            time.sleep(0.5)

        except Exception as e:
            print("Error general:", e)
            time.sleep(2)


if __name__ == "__main__":
    run()
