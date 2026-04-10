import time
import os
import requests
import sys
from iqoptionapi.stable_api import IQ_Option

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)

from estrategia import detectar_entrada_oculta

EMAIL = os.getenv("IQ_EMAIL")
PASSWORD = os.getenv("IQ_PASSWORD")

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

MONTO = 5000
CUENTA = "PRACTICE"

# 🔥 SOLO UN PAR
PARES = ["EURUSD-OTC"]


# =========================
# TELEGRAM
# =========================
def enviar_mensaje(texto):
    try:
        requests.post(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            data={"chat_id": CHAT_ID, "text": texto},
            timeout=5
        )
    except:
        pass


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
                print("✅ CONECTADO")
                return iq

        except:
            pass

        time.sleep(5)


# =========================
# VALIDAR OTC
# =========================
def par_abierto(iq, par):
    try:
        activos = iq.get_all_open_time()
        return activos["digital"][par]["open"]
    except:
        return False


# =========================
# DATOS (3 HORAS)
# =========================
def obtener_velas(iq, par):
    try:
        velas = iq.get_candles(par, 60, 180, time.time())

        return [{
            "open": v["open"],
            "close": v["close"],
            "max": v["max"],
            "min": v["min"]
        } for v in velas]

    except:
        return []


# =========================
# OPERAR INMEDIATO
# =========================
def operar(iq, par, direccion):

    if not par_abierto(iq, par):
        return False

    try:
        status, _ = iq.buy_digital_spot(par, MONTO, direccion, 1)

        if status:
            print(f"🚀 {par} {direccion}")

            enviar_mensaje(f"""
🚀 ENTRADA CORRECCIÓN

Par: {par}
Dirección: {direccion.upper()}
Expiración: 1 MIN
Monto: ${MONTO}

📊 Estrategia: Pullback + Continuidad
""")

            return True

    except:
        pass

    return False


# =========================
# MAIN
# =========================
def run():

    iq = conectar()
    ultima_operacion = 0

    while True:
        try:
            if time.time() - ultima_operacion < 30:
                time.sleep(0.2)
                continue

            data = {}

            for par in PARES:
                data[par] = obtener_velas(iq, par)

            señal = detectar_entrada_oculta(data)

            if señal:
                par, direccion, score = señal

                print(f"🎯 {par} {direccion}")

                if operar(iq, par, direccion):
                    ultima_operacion = time.time()
                    time.sleep(60)

            else:
                time.sleep(0.2)

        except:
            iq = conectar()
            time.sleep(5)


if __name__ == "__main__":
    run()
