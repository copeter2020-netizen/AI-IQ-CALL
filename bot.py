import time
import os
import requests
from iqoptionapi.stable_api import IQ_Option
from estrategia import detectar_mejor_entrada

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
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": texto})


def leer_comandos():
    global bot_activo, last_update_id

    try:
        url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
        data = requests.get(url).json()

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

    except:
        pass


# =========================
# CONEXIÓN
# =========================
def conectar():
    while True:
        iq = IQ_Option(EMAIL, PASSWORD)
        iq.connect()

        if iq.check_connect():
            iq.change_balance(CUENTA)
            return iq

        time.sleep(5)


# =========================
# VELAS
# =========================
def obtener_velas(iq, par):
    velas = iq.get_candles(par, 60, 40, time.time())

    return [{
        "open": v["open"],
        "close": v["close"],
        "max": v["max"],
        "min": v["min"]
    } for v in velas]


# =========================
# OPERAR
# =========================
def operar(iq, par, direccion):

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


if __name__ == "__main__":
    run()
