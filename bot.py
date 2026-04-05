import time
import os
import requests
import sys
from iqoptionapi.stable_api import IQ_Option

# =========================
# 🔥 FIX PATH (Railway)
# =========================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)

# =========================
# 🔥 IMPORT SEGURO
# =========================
try:
    from estrategia import detectar_entrada_oculta
except Exception as e:
    print("❌ Error importando estrategia:", e)
    detectar_entrada_oculta = None


# =========================
# CONFIG
# =========================
EMAIL = os.getenv("IQ_EMAIL")
PASSWORD = os.getenv("IQ_PASSWORD")

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

MONTO = 1750
CUENTA = "PRACTICE"

PARES = [
    "EURUSD-OTC",
    "GBPUSD-OTC",
    "EURJPY-OTC",
    "EURGBP-OTC",
    "GBPJPY-OTC",
    "USDCHF-OTC"
]


# =========================
# TELEGRAM
# =========================
def enviar_mensaje(texto):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        requests.post(url, data={
            "chat_id": CHAT_ID,
            "text": texto
        }, timeout=5)
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

        except Exception as e:
            print("Error conexión:", e)

        time.sleep(5)


# =========================
# ⏱️ ESPERAR APERTURA REAL
# =========================
def esperar_apertura_vela():
    while True:
        segundos = int(time.time()) % 60

        # Entrada EXACTA en apertura
        if segundos == 0:
            return

        time.sleep(0.2)


# =========================
# VELAS
# =========================
def obtener_velas(iq, par):
    try:
        velas = iq.get_candles(par, 60, 40, time.time())

        return [{
            "open": v["open"],
            "close": v["close"],
            "max": v["max"],
            "min": v["min"]
        } for v in velas]

    except Exception as e:
        print("Error velas:", e)
        return []


# =========================
# OPERAR
# =========================
def operar(iq, par, direccion):

    try:
        esperar_apertura_vela()

        check, _ = iq.buy(MONTO, par, direccion, 3)

        if check:
            print(f"🚀 ENTRADA {par} {direccion}")

            enviar_mensaje(f"""
🚀 ENTRADA PRO

Par: {par}
Dirección: {direccion.upper()}
Expiración: 3 MIN
Monto: ${MONTO}

⏱ Entrada en apertura REAL
""")

    except Exception as e:
        print("Error operar:", e)


# =========================
# LOOP
# =========================
def run():

    if detectar_entrada_oculta is None:
        print("❌ No se puede ejecutar sin estrategia.py")
        return

    iq = conectar()

    while True:
        try:

            data = {}

            for par in PARES:
                data[par] = obtener_velas(iq, par)

            señal = detectar_entrada_oculta(data)

            if señal:
                par, direccion, score = señal

                print(f"🎯 Señal {par} {direccion} Score:{score}")

                operar(iq, par, direccion)

                time.sleep(180)

            else:
                time.sleep(0.5)

        except Exception as e:
            print("Error loop:", e)
            time.sleep(5)


# =========================
# START
# =========================
if __name__ == "__main__":
    run()
