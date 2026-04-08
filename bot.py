import time
import os
import requests
from iqoptionapi.stable_api import IQ_Option
from estrategia import detectar_entrada_oculta


EMAIL = os.getenv("IQ_EMAIL")
PASSWORD = os.getenv("IQ_PASSWORD")

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

MONTO = 15000
CUENTA = "PRACTICE"

PARES = [
    "EURUSD-OTC",
    "EURJPY-OTC",
    "EURGBP-OTC",
    "GBPUSD-OTC",
    "USDJPY-OTC"
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

        except:
            time.sleep(5)


# =========================
# TIEMPO EXACTO
# =========================
def esperar_cierre_vela():
    while True:
        ahora = time.time()
        if int(ahora) % 60 == 0:
            return
        time.sleep(0.01)


# =========================
# DATOS
# =========================
def obtener_velas(iq, par):
    try:
        velas = iq.get_candles(par, 60, 50, time.time())

        return [{
            "open": v["open"],
            "close": v["close"],
            "max": v["max"],
            "min": v["min"]
        } for v in velas]

    except:
        return []


# =========================
# OPERAR
# =========================
def operar(iq, par, direccion):

    esperar_cierre_vela()

    check, _ = iq.buy(MONTO, par, direccion, 3)

    if check:
        print(f"🚀 {par} {direccion}")

        enviar_mensaje(f"""
🚀 ENTRADA BREAKOUT

Par: {par}
Dirección: {direccion.upper()}
Expiración: 3 MIN
Monto: ${MONTO}
""")


# =========================
# LOOP
# =========================
def run():

    iq = conectar()

    while True:
        try:
            data = {}

            for par in PARES:
                data[par] = obtener_velas(iq, par)

            señal = detectar_entrada_oculta(data)

            if señal:
                par, direccion, score = señal

                print(f"🎯 {par} {direccion} Score:{score}")

                operar(iq, par, direccion)

                time.sleep(180)

            else:
                time.sleep(0.5)

        except Exception as e:
            print("Error:", e)
            time.sleep(5)


if __name__ == "__main__":
    run()
