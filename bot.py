import time
import os
import requests
from iqoptionapi.stable_api import IQ_Option
from estrategia import analyze_market

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
    "EURGBP-OTC",
    "GBPJPY-OTC",
    "USDZAR-OTC",
    "USDHKD-OTC",
    "USDINR-OTC",
    "USDTRY-OTC",
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

        for update in data["result"]:

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
        iq = IQ_Option(EMAIL, PASSWORD)
        iq.connect()

        if iq.check_connect():
            iq.change_balance(CUENTA)
            print("✅ CONECTADO")
            return iq

        print("❌ Error conexión")
        time.sleep(10)


# =========================
# VELAS
# =========================
def obtener_velas(iq, par):
    velas = iq.get_candles(par, 60, 30, time.time())

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

    check, _ = iq.buy(MONTO, par, direccion, 4)  # 🔥 4 MIN

    if check:
        enviar_mensaje(f"""
🚀 ENTRADA PRO

Par: {par}
Dirección: {direccion.upper()}
Expiración: 4 MIN
Monto: ${MONTO}
""")
    else:
        print("❌ Error operación")


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

            for par in PARES:

                velas = obtener_velas(iq, par)

                señal = analyze_market(velas, None, None)

                if señal:

                    direccion = señal["action"]

                    segundos = int(time.time()) % 60
                    esperar = 60 - segundos

                    if esperar > 0:
                        time.sleep(esperar)

                    operar(iq, par, direccion)

                    time.sleep(240)  # 🔥 4 min

            time.sleep(2)

        except Exception as e:
            print("ERROR:", e)
            time.sleep(5)


# =========================
# START
# =========================
if __name__ == "__main__":
    run()
