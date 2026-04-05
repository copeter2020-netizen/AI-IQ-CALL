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
# UTILIDADES
# =========================
def body(c):
    return abs(c["close"] - c["open"])

def rango(c):
    return c["max"] - c["min"]

def vela_fuerte(c):
    return body(c) > rango(c) * 0.6


# =========================
# FILTROS PRO
# =========================
def rechazo_fuerte(v):
    return (
        (v["max"] - max(v["open"], v["close"])) > body(v) * 1.2 and
        v["close"] < v["open"]
    )

def agotamiento_previo(df):
    v1 = df.iloc[-2]
    v2 = df.iloc[-3]

    return (
        body(v1) < body(v2) and
        (
            (v1["max"] - max(v1["open"], v1["close"])) > body(v1) or
            (min(v1["open"], v1["close"]) - v1["min"]) > body(v1)
        )
    )

def entrada_explotada(df, rango_total):
    mov = abs(df["close"].iloc[-1] - df["close"].iloc[-2])
    return mov > rango_total * 0.25


# 🔥 NUEVO: FILTRO DE TENDENCIA
def tendencia_general(df):
    return df["close"].iloc[-1] > df["close"].iloc[-5]


# =========================
# ESTRATEGIA SNIPER
# =========================
def detectar_entrada(data):

    mejor = None
    mejor_score = 0

    for par, velas in data.items():

        df = pd.DataFrame(velas)

        if len(df) < 30:
            continue

        soporte = df["min"].rolling(20).min().iloc[-1]
        resistencia = df["max"].rolling(20).max().iloc[-1]

        rango_total = max(df["max"][-20:]) - min(df["min"][-20:])

        prev = df.iloc[-2]
        v = df.iloc[-1]

        if rango(v) == 0:
            continue

        score = 0

        # ======================
        # FILTROS CLAVE
        # ======================
        if entrada_explotada(df, rango_total):
            continue

        if rechazo_fuerte(v):
            continue

        # ======================
        # SOPORTE → CALL
        # ======================
        if abs(prev["min"] - soporte) < rango_total * 0.05:

            # filtro tendencia (solo compras en tendencia alcista)
            if not tendencia_general(df):
                continue

            if vela_fuerte(v):
                continue

            if body(prev) < rango(prev) * 0.4:
                score += 2

            if v["close"] > v["open"] and body(v) > rango(v) * 0.4:
                score += 2

            if v["close"] > prev["close"]:
                score += 1

            if agotamiento_previo(df):
                score += 2

            direccion = "call"

        # ======================
        # RESISTENCIA → PUT
        # ======================
        elif abs(prev["max"] - resistencia) < rango_total * 0.05:

            # filtro tendencia (solo ventas en tendencia bajista)
            if tendencia_general(df):
                continue

            if vela_fuerte(v):
                continue

            if body(prev) < rango(prev) * 0.4:
                score += 2

            if v["close"] < v["open"] and body(v) > rango(v) * 0.4:
                score += 2

            if v["close"] < prev["close"]:
                score += 1

            if agotamiento_previo(df):
                score += 2

            direccion = "put"

        else:
            continue

        if score > mejor_score:
            mejor_score = score
            mejor = (par, direccion)

    if mejor and mejor_score >= 4:
        return mejor

    return None


# =========================
# OPERAR
# =========================
def operar(iq, par, direccion):

    try:
        check, _ = iq.buy(MONTO, par, direccion, 3)

        if check:
            print(f"🚀 ENTRADA {par} {direccion}")

            enviar_mensaje(f"""
🚀 ENTRADA SNIPER

Par: {par}
Dirección: {direccion.upper()}
Expiración: 3 MIN
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

            señal = detectar_entrada(data)

            if señal:
                par, direccion = señal

                operar(iq, par, direccion)

                time.sleep(180)

            else:
                time.sleep(1)

        except:
            time.sleep(5)


# =========================
# START
# =========================
if __name__ == "__main__":
    run()
