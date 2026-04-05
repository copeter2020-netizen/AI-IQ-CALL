import time
import os
import requests
import pandas as pd
import numpy as np
from iqoptionapi.stable_api import IQ_Option

# =========================
# CONFIG
# =========================
EMAIL = os.getenv("IQ_EMAIL")
PASSWORD = os.getenv("IQ_PASSWORD")

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

MONTO = 1750
CUENTA = "PRACTICE"

EXPIRACION = 3  # 🔥 3 minutos fijo

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

        except:
            pass

        time.sleep(5)


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

    except:
        return []


# =========================
# ⏱️ ESPERAR APERTURA EXACTA
# =========================
def esperar_apertura_vela():
    while True:
        segundos = int(time.time()) % 60

        # entrar justo en segundo 0-1
        if segundos == 0 or segundos == 1:
            return

        time.sleep(0.2)


# =========================
# 🔥 ESTRATEGIA (LLAMA TU ARCHIVO)
# =========================
from estrategia import detectar_entrada_oculta


# =========================
# OPERAR
# =========================
def operar(iq, par, direccion):

    try:
        # 🔥 ENTRAR EXACTO EN APERTURA
        esperar_apertura_vela()

        check, _ = iq.buy(MONTO, par, direccion, EXPIRACION)

        if check:
            print(f"🚀 ENTRADA {par} {direccion}")

            enviar_mensaje(f"""
🚀 ENTRADA SNIPER

Par: {par}
Dirección: {direccion.upper()}
Expiración: {EXPIRACION} MIN
Entrada: APERTURA DE VELA
Monto: ${MONTO}
""")

    except:
        pass


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
                par, direccion, _ = señal

                operar(iq, par, direccion)

                # esperar cierre de operación
                time.sleep(EXPIRACION * 60)

            else:
                time.sleep(0.5)

        except:
            time.sleep(5)


# =========================
# START
# =========================
if __name__ == "__main__":
    run()
