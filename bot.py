import time
import os
import requests
import pandas as pd
import numpy as np
from iqoptionapi.stable_api import IQ_Option

# =========================
# VARIABLES
# =========================
EMAIL = os.getenv("IQ_EMAIL")
PASSWORD = os.getenv("IQ_PASSWORD")

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

MONTO = 10080
CUENTA = "PRACTICE"

PARES = [
    "EURUSD-OTC",
    "GBPUSD-OTC",
    "EURJPY-OTC",
    "USDCHF-OTC"
]

bot_activo = True
last_update_id = None


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
    except Exception as e:
        print("Error Telegram:", e)


def leer_comandos():
    global bot_activo, last_update_id

    try:
        url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
        data = requests.get(url, timeout=5).json()

        for update in data.get("result", []):

            update_id = update["update_id"]

            if last_update_id and update_id <= last_update_id:
                continue

            last_update_id = update_id

            if "message" in update:
                texto = update["message"].get("text", "")

                if texto == "/startbot":
                    bot_activo = True
                    enviar_mensaje("✅ BOT ACTIVADO")

                elif texto == "/stopbot":
                    bot_activo = False
                    enviar_mensaje("⛔ BOT DETENIDO")

    except Exception as e:
        print("Error comandos:", e)


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

            print("❌ Error conexión")
            time.sleep(5)

        except Exception as e:
            print("Error conexión:", e)
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

    except Exception as e:
        print("Error velas:", e)
        return []


# =========================
# 🔥 ESTRATEGIA SNIPER (INLINE)
# =========================
def body(c):
    return abs(c["close"] - c["open"])

def rango(c):
    return c["max"] - c["min"]

def mecha_sup(c):
    return c["max"] - max(c["open"], c["close"])

def mecha_inf(c):
    return min(c["open"], c["close"]) - c["min"]

def es_alcista(c):
    return c["close"] > c["open"]

def es_bajista(c):
    return c["close"] < c["open"]


def mercado_activo(df):
    highs = df["max"].values
    lows = df["min"].values

    vol_actual = np.mean(highs[-5:] - lows[-5:])
    vol_pasada = np.mean(highs[-30:] - lows[-30:])

    rango_total = max(highs[-20:]) - min(lows[-20:])

    if vol_actual < vol_pasada * 0.8:
        return False

    if rango_total < vol_actual * 2:
        return False

    return True


def detectar_mejor_entrada(data_por_par):

    mejor = None
    mejor_score = 0

    for par, velas in data_por_par.items():

        df = pd.DataFrame(velas)

        if len(df) < 30:
            continue

        if not mercado_activo(df):
            continue

        soporte = df["min"].rolling(20).min().iloc[-1]
        resistencia = df["max"].rolling(20).max().iloc[-1]

        c1 = df.iloc[-1]
        c2 = df.iloc[-2]

        score = 0

        # ======================
        # CALL
        # ======================
        if c2["min"] <= soporte:

            if mecha_inf(c2) > body(c2) * 1.5:

                if es_alcista(c1) and body(c1) > rango(c1) * 0.6:
                    score += 3

                    if score > mejor_score:
                        mejor_score = score
                        mejor = (par, "call", score)

        # ======================
        # PUT
        # ======================
        if c2["max"] >= resistencia:

            if mecha_sup(c2) > body(c2) * 1.5:

                if es_bajista(c1) and body(c1) > rango(c1) * 0.6:
                    score += 3

                    if score > mejor_score:
                        mejor_score = score
                        mejor = (par, "put", score)

    if mejor:
        return mejor

    return None


# =========================
# OPERAR
# =========================
def operar(iq, par, direccion):
    try:
        print(f"🔥 {par} → {direccion}")

        check, _ = iq.buy(MONTO, par, direccion, 4)

        if check:
            enviar_mensaje(f"""
🚀 ENTRADA SNIPER

Par: {par}
Dirección: {direccion.upper()}
Expiración: 4 MIN
Monto: ${MONTO}
""")
        else:
            print("❌ No ejecutada")

    except Exception as e:
        print("Error operación:", e)


# =========================
# LOOP
# =========================
def run():

    iq = conectar()

    while True:
        try:

            leer_comandos()

            if not bot_activo:
                print("⏸ BOT PAUSADO")
                time.sleep(2)
                continue

            data = {}

            for par in PARES:
                data[par] = obtener_velas(iq, par)

            resultado = detectar_mejor_entrada(data)

            if resultado:
                par, direccion, score = resultado

                print(f"✅ SETUP TOP ({score})")

                segundos = int(time.time()) % 60
                esperar = 60 - segundos

                if esperar > 0:
                    time.sleep(esperar)

                operar(iq, par, direccion)

                time.sleep(240)

            else:
                print("🔎 Buscando condiciones PERFECTAS...")

            time.sleep(2)

        except Exception as e:
            print("ERROR:", e)
            time.sleep(5)


# =========================
# START
# =========================
if __name__ == "__main__":
    run()
