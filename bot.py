import time
import os
import requests
import pandas as pd
from iqoptionapi.stable_api import IQ_Option

# =========================
# VARIABLES
# =========================
EMAIL = os.getenv("IQ_EMAIL")
PASSWORD = os.getenv("IQ_PASSWORD")

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

MONTO = 1000
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
        r = requests.get(url, timeout=5)
        data = r.json()

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
                print("✅ CONECTADO")
                iq.change_balance(CUENTA)
                return iq

            print("❌ Error conexión")
            time.sleep(10)

        except Exception as e:
            print("Error conexión:", e)
            time.sleep(10)


# =========================
# VELAS
# =========================
def obtener_velas(iq, par):
    try:
        velas = iq.get_candles(par, 60, 30, time.time())

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
# 🧠 ESTRATEGIA (DENTRO DEL BOT)
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


def niveles(df):
    soporte = df["min"].rolling(20).min().iloc[-1]
    resistencia = df["max"].rolling(20).max().iloc[-1]
    return soporte, resistencia


def rechazo_soporte(c):
    return mecha_inf(c) > body(c) * 1.5

def rechazo_resistencia(c):
    return mecha_sup(c) > body(c) * 1.5


def continuidad_alcista(c):
    r = rango(c)
    if r == 0:
        return False
    pos = (c["close"] - c["min"]) / r
    return es_alcista(c) and pos > 0.7 and body(c) > r * 0.5


def continuidad_bajista(c):
    r = rango(c)
    if r == 0:
        return False
    pos = (c["close"] - c["min"]) / r
    return es_bajista(c) and pos < 0.3 and body(c) > r * 0.5


def detectar_entrada(velas):
    try:
        df = pd.DataFrame(velas)

        if len(df) < 25:
            return None

        soporte = df["min"].rolling(20).min().iloc[-1]
        resistencia = df["max"].rolling(20).max().iloc[-1]

        c1 = df.iloc[-1]
        c2 = df.iloc[-2]

        # CALL
        if c2["min"] <= soporte:
            if rechazo_soporte(c2) and continuidad_alcista(c1):
                return "call"

        # PUT
        if c2["max"] >= resistencia:
            if rechazo_resistencia(c2) and continuidad_bajista(c1):
                return "put"

        return None

    except Exception as e:
        print("Error estrategia:", e)
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
🚀 ENTRADA PRO

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

            for par in PARES:

                velas = obtener_velas(iq, par)

                señal = detectar_entrada(velas)

                if señal:
                    segundos = int(time.time()) % 60
                    esperar = 60 - segundos

                    if esperar > 0:
                        time.sleep(esperar)

                    operar(iq, par, señal)

                    time.sleep(240)

            time.sleep(2)

        except Exception as e:
            print("ERROR LOOP:", e)
            time.sleep(5)


# =========================
# START
# =========================
if __name__ == "__main__":
    run()
