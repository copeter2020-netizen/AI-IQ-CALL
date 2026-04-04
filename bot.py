import time
import os
import requests
from iqoptionapi.stable_api import IQ_Option
from estrategia import detectar_entrada_oculta

# =========================
# VARIABLES
# =========================
EMAIL = os.getenv("IQ_EMAIL")
PASSWORD = os.getenv("IQ_PASSWORD")

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

MONTO = 1700
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
        })
    except:
        pass


def leer_comandos():
    global bot_activo, last_update_id

    try:
        url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
        data = requests.get(url).json()

        for u in data.get("result", []):

            if last_update_id and u["update_id"] <= last_update_id:
                continue

            last_update_id = u["update_id"]

            if "message" in u:
                txt = u["message"].get("text", "")

                if txt == "/startbot":
                    bot_activo = True
                    enviar_mensaje("✅ BOT ACTIVADO")

                elif txt == "/stopbot":
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
            print("✅ CONECTADO")
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

    check, _ = iq.buy(MONTO, par, direccion, 4)

    if check:
        print("✅ EJECUTADA")

        enviar_mensaje(f"""
🚀 ENTRADA OCULTA

Par: {par}
Dirección: {direccion.upper()}
Expiración: 4 MIN
Monto: ${MONTO}
""")
    else:
        print("❌ FALLÓ")


# =========================
# LOOP
# =========================
def run():

    iq = conectar()

    while True:
        try:

            leer_comandos()

            if not bot_activo:
                time.sleep(1)
                continue

            data = {}

            for par in PARES:
                data[par] = obtener_velas(iq, par)

            resultado = detectar_entrada_oculta(data)

            if resultado:
                par, direccion, score = resultado

                print(f"🔥 ENTRADA OCULTA ({score})")

                operar(iq, par, direccion)

                time.sleep(240)

            else:
                print("🔎 Esperando entrada oculta...")

            time.sleep(1)

        except Exception as e:
            print("ERROR:", e)
            time.sleep(5)


if __name__ == "__main__":
    run()
