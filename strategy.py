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
# VELAS
# =========================
def obtener_velas(iq, par):
    try:
        velas = iq.get_candles(par, 60, 180, time.time())  # 🔥 40 → 180

        return [{
            "open": v["open"],
            "close": v["close"],
            "max": v["max"],
            "min": v["min"]
        } for v in velas]

    except:
        return []


# =========================
# ⏱️ EXPIRACIÓN DINÁMICA
# =========================
def calcular_expiracion(df):

    volatilidad = np.mean(df["max"].iloc[-5:] - df["min"].iloc[-5:])

    if volatilidad > 0.0005:
        return 2  # mercado rápido
    else:
        return 3  # mercado lento


# =========================
# 🔥 ENTRADA MEJORADA
# =========================
def detectar_entrada(data):

    mejor = None
    mejor_score = 0
    mejor_df = None

    for par, velas in data.items():

        df = pd.DataFrame(velas)

        if len(df) < 30:
            continue

        soporte = df["min"].rolling(20).min().iloc[-1]
        resistencia = df["max"].rolling(20).max().iloc[-1]

        rango_total = max(df["max"][-20:]) - min(df["min"][-20:])

        v = df.iloc[-1]

        cuerpo = abs(v["close"] - v["open"])
        rango = v["max"] - v["min"]

        if rango == 0:
            continue

        mecha_sup = v["max"] - max(v["open"], v["close"])
        mecha_inf = min(v["open"], v["close"]) - v["min"]

        # =========================
        # 🔥 FILTROS NUEVOS
        # =========================
        mov = abs(df["close"].iloc[-1] - df["close"].iloc[-5])
        if mov > rango_total * 0.6:
            continue  # mercado estirado

        ultimas = df.iloc[-5:]
        verdes = sum(ultimas["close"] > ultimas["open"])
        rojas = sum(ultimas["close"] < ultimas["open"])

        if verdes >= 4 or rojas >= 4:
            continue  # secuencia fuerte (entrada tardía)

        # ======================
        # SOPORTE → CALL
        # ======================
        if abs(v["min"] - soporte) < rango_total * 0.05:

            confirmaciones = 0

            if mecha_inf > cuerpo:
                confirmaciones += 1

            if v["close"] > v["open"] and cuerpo > rango * 0.5:
                confirmaciones += 1

            if v["close"] > df["close"].iloc[-2]:
                confirmaciones += 1

            if confirmaciones >= 2:
                direccion = "call"
                score = confirmaciones

            else:
                continue

        # ======================
        # RESISTENCIA → PUT
        # ======================
        elif abs(v["max"] - resistencia) < rango_total * 0.05:

            confirmaciones = 0

            if mecha_sup > cuerpo:
                confirmaciones += 1

            if v["close"] < v["open"] and cuerpo > rango * 0.5:
                confirmaciones += 1

            if v["close"] < df["close"].iloc[-2]:
                confirmaciones += 1

            if confirmaciones >= 2:
                direccion = "put"
                score = confirmaciones

            else:
                continue

        else:
            continue

        if score > mejor_score:
            mejor_score = score
            mejor = (par, direccion)
            mejor_df = df

    if mejor and mejor_score >= 2:
        return mejor, mejor_df

    return None, None


# =========================
# OPERAR
# =========================
def operar(iq, par, direccion, df):

    try:
        expiracion = calcular_expiracion(df)

        check, _ = iq.buy(MONTO, par, direccion, expiracion)

        if check:
            print(f"🚀 ENTRADA {par} {direccion}")

            enviar_mensaje(f"""
🚀 ENTRADA

Par: {par}
Dirección: {direccion.upper()}
Expiración: {expiracion} MIN
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

            señal, df = detectar_entrada(data)

            if señal:
                par, direccion = señal

                operar(iq, par, direccion, df)

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
