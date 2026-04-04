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

MONTO = 3333
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

            time.sleep(5)

        except Exception as e:
            print("Error conexión:", e)
            time.sleep(5)


# =========================
# VALIDAR PAR
# =========================
def par_abierto(iq, par):
    try:
        activos = iq.get_all_open_time()
        return activos["binary"][par]["open"]
    except:
        return False


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
# ESTRATEGIA
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


def detectar_mejor_entrada(data):

    mejor = None
    mejor_score = 0

    for par, velas in data.items():

        df = pd.DataFrame(velas)

        if len(df) < 30:
            continue

        soporte = df["min"].rolling(20).min().iloc[-1]
        resistencia = df["max"].rolling(20).max().iloc[-1]

        c1 = df.iloc[-1]
        c2 = df.iloc[-2]

        score = 0

        # CALL
        if c2["min"] <= soporte:
            if mecha_inf(c2) > body(c2) * 1.5:
                if es_alcista(c1) and body(c1) > rango(c1) * 0.6:
                    score += 3

        # PUT
        if c2["max"] >= resistencia:
            if mecha_sup(c2) > body(c2) * 1.5:
                if es_bajista(c1) and body(c1) > rango(c1) * 0.6:
                    score += 3

        if score > mejor_score:
            mejor_score = score
            mejor = (par, "call" if es_alcista(c1) else "put", score)

    return mejor


# =========================
# OPERAR (MEJORADO)
# =========================
def operar(iq, par, direccion):

    if not par_abierto(iq, par):
        print(f"⛔ {par} cerrado")
        return False

    for intento in range(3):

        check, id = iq.buy(MONTO, par, direccion, 4)

        if check:
            print("✅ OPERACIÓN EJECUTADA")

            enviar_mensaje(f"""
🚀 ENTRADA REAL

Par: {par}
Dirección: {direccion.upper()}
Expiración: 4 MIN
Monto: ${MONTO}
""")
            return True

        print(f"⚠️ Reintento {intento+1}")
        time.sleep(1)

    print("❌ FALLÓ OPERACIÓN")
    return False


# =========================
# LOOP
# =========================
def run():

    iq = conectar()

    while True:
        try:

            leer_comandos()

            if not bot_activo:
                time.sleep(2)
                continue

            data = {}

            for par in PARES:
                data[par] = obtener_velas(iq, par)

            resultado = detectar_mejor_entrada(data)

            if resultado:
                par, direccion, score = resultado

                print(f"🔥 SETUP TOP ({score})")

                # 🔥 TIMING REAL
                while True:
                    if time.time() % 60 >= 59.7:
                        break

                operar(iq, par, direccion)

                time.sleep(240)

            else:
                print("🔎 Buscando condiciones PERFECTAS...")

            time.sleep(1)

        except Exception as e:
            print("ERROR:", e)
            time.sleep(5)


# =========================
# START
# =========================
if __name__ == "__main__":
    run()
