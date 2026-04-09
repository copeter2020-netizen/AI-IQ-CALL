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

MONTO = float(os.getenv("MONTO", 5))
CUENTA = os.getenv("CUENTA", "PRACTICE")

PARES = [
    "EURUSD-OTC",
    "EURJPY-OTC",
    "GBPUSD-OTC"
]


# =========================
# TELEGRAM
# =========================
def enviar_mensaje(texto):
    if not TOKEN or not CHAT_ID:
        return

    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        requests.post(url, data={
            "chat_id": CHAT_ID,
            "text": texto
        }, timeout=5)
    except:
        pass  # 🔥 silencio total


# =========================
# CONEXIÓN (SIN SPAM)
# =========================
def conectar():
    while True:
        try:
            iq = IQ_Option(EMAIL, PASSWORD)
            iq.connect()

            if iq.check_connect():
                iq.change_balance(CUENTA)

                print("✅ CONECTADO")
                enviar_mensaje("✅ BOT CONECTADO")

                return iq

        except:
            pass

        time.sleep(5)


# =========================
# TIEMPO
# =========================
def esperar_cierre():
    while True:
        now = time.time()
        if int(now) % 60 == 59:
            return
        time.sleep(0.05)


# =========================
# DATOS (SILENCIOSO)
# =========================
def obtener_velas(iq, par):
    try:
        velas = iq.get_candles(par, 60, 60, time.time())

        if not velas or len(velas) < 30:
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
# VALIDAR OTC
# =========================
def par_disponible(iq, par):
    try:
        return iq.get_all_open_time()["digital"][par]["open"]
    except:
        return False


# =========================
# OPERAR (SIN SPAM)
# =========================
def operar(iq, par, direccion):

    if not par_disponible(iq, par):
        return False

    esperar_cierre()

    try:
        status, _ = iq.buy_digital_spot(par, MONTO, direccion, 5)

        if status:
            print(f"🚀 {par} {direccion}")

            enviar_mensaje(f"""
🚀 ENTRADA

Par: {par}
Dirección: {direccion.upper()}
Expiración: 5 MIN
Monto: ${MONTO}
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
            if time.time() - ultima_operacion < 60:
                time.sleep(0.5)
                continue

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

                print(f"🎯 {par} {direccion}")

                enviar_mensaje(f"🎯 SEÑAL {par} {direccion.upper()}")

                ejecutado = operar(iq, par, direccion)

                if ejecutado:
                    ultima_operacion = time.time()
                    time.sleep(300)

            else:
                time.sleep(0.5)

        except:
            # 🔥 silencio total + reconexión limpia
            iq = conectar()
            time.sleep(5)


if __name__ == "__main__":
    run()
