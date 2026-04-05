import time
import os
import requests
import pandas as pd
import numpy as np
from iqoptionapi.stable_api import IQ_Option

# 🔥 FIX IMPORT (Railway)
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from estrategia import detectar_entrada_oculta


# =========================
# CONFIG
# =========================
EMAIL = os.getenv("IQ_EMAIL")
PASSWORD = os.getenv("IQ_PASSWORD")

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

MONTO = 17500
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

        except:
            pass

        time.sleep(5)


# =========================
# ⏱️ ESPERAR APERTURA VELA
# =========================
def esperar_apertura_vela():
    while True:
        segundos = int(time.time()) % 60

        # Espera justo a que abra la vela
        if segundos == 0:
            return

        time.sleep(0.3)


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
# OPERAR (ENTRADA PERFECTA)
# =========================
def operar(iq, par, direccion):

    try:
        # 🔥 ENTRAR JUSTO EN APERTURA
        esperar_apertura_vela()

        check, _ = iq.buy(MONTO, par, direccion, 3)

        if check:
            print(f"🚀 ENTRADA PERFECTA {par} {direccion}")

            enviar_mensaje(f"""
🚀 ENTRADA SNIPER

Par: {par}
Dirección: {direccion.upper()}
Expiración: 3 MIN
Monto: ${MONTO}

⏱ Entrada EXACTA en apertura de vela
""")

    except:
        pass


# =========================
# LOOP PRINCIPAL
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

                print(f"🎯 Señal detectada {par} {direccion} Score: {score}")

                operar(iq, par, direccion)

                # Esperar cierre operación (3 min)
                time.sleep(180)

            else:
                time.sleep(0.5)

        except Exception as e:
            print("Error:", e)
            time.sleep(5)


# =========================
# START
# =========================
if __name__ == "__main__":
    run()
