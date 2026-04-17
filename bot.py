import time
import os
import requests
import sys
import threading
from iqoptionapi.stable_api import IQ_Option

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)

from estrategia import detectar_entrada_oculta

# =========================
# VARIABLES
# =========================
EMAIL = os.getenv("IQ_EMAIL")
PASSWORD = os.getenv("IQ_PASSWORD")
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

MONTO = 500
CUENTA = "PRACTICE"

ultima_entrada = 0
bot_activo = False
update_id = None

par_seleccionado = None


# =========================
# TELEGRAM
# =========================
def enviar_telegram(msg):
    def enviar():
        try:
            requests.post(
                f"https://api.telegram.org/bot{TOKEN}/sendMessage",
                data={"chat_id": CHAT_ID, "text": msg},
                timeout=5
            )
        except:
            pass

    threading.Thread(target=enviar, daemon=True).start()


def enviar_panel():
    keyboard = {
        "keyboard": [
            ["💱 EURUSD", "💱 GBPUSD"],
            ["💱 EURJPY", "💱 USDCHF"],
            ["💱 GBPJPY", "💱 USDZAR"],
            ["▶️ Activar", "⛔ Detener"]
        ],
        "resize_keyboard": True
    }

    try:
        requests.post(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            json={
                "chat_id": CHAT_ID,
                "text": "📊 PANEL DE CONTROL",
                "reply_markup": keyboard
            },
            timeout=5
        )
    except:
        pass


def verificar_comandos():
    global bot_activo, update_id, par_seleccionado

    try:
        url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
        params = {"timeout": 1, "offset": update_id}

        res = requests.get(url, params=params, timeout=3).json()

        if "result" not in res:
            return

        for update in res["result"]:
            update_id = update["update_id"] + 1

            if "message" not in update:
                continue

            msg = update["message"].get("text", "")

            if msg == "/start":
                enviar_panel()

            elif "EURUSD" in msg:
                par_seleccionado = "EURUSD-OTC"
                enviar_telegram("Par seleccionado EURUSD")

            elif "GBPUSD" in msg:
                par_seleccionado = "GBPUSD-OTC"
                enviar_telegram("Par seleccionado GBPUSD")

            elif "EURJPY" in msg:
                par_seleccionado = "EURJPY-OTC"

            elif "USDCHF" in msg:
                par_seleccionado = "USDCHF-OTC"

            elif "GBPJPY" in msg:
                par_seleccionado = "GBPJPY-OTC"

            elif "USDZAR" in msg:
                par_seleccionado = "USDZAR-OTC"

            elif msg == "▶️ Activar":
                bot_activo = True
                enviar_telegram("🟢 BOT ACTIVADO")

            elif msg == "⛔ Detener":
                bot_activo = False
                enviar_telegram("🔴 BOT DETENIDO")

    except:
        pass


def log(msg):
    print(msg)
    enviar_telegram(msg)


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
                log("✅ BOT CONECTADO")
                return iq

        except:
            pass

        time.sleep(5)


def asegurar_conexion(iq):
    try:
        if not iq.check_connect():
            return conectar()
        return iq
    except:
        return conectar()


# =========================
# DATOS
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
    except:
        return None


# =========================
# OPERAR
# =========================
def operar(iq, par, direccion):
    global ultima_entrada

    if time.time() - ultima_entrada < 20:
        return

    try:
        status, order_id = iq.buy(MONTO, par, direccion, 1)

        if status:
            log(f"""🚀 OPERACIÓN

{par} {direccion.upper()}
ID: {order_id}
""")
            ultima_entrada = time.time()

    except:
        pass


# =========================
# MAIN
# =========================
def run():

    iq = conectar()

    while True:
        try:
            verificar_comandos()

            if not bot_activo or not par_seleccionado:
                time.sleep(1)
                continue

            iq = asegurar_conexion(iq)

            velas = obtener_velas(iq, par_seleccionado)

            if not velas:
                continue

            señal = detectar_entrada_oculta({par_seleccionado: velas})

            if señal:
                par, direccion, score = señal

                log(f"""📈 SEÑAL

Par: {par}
Dirección: {direccion.upper()}
Score: {score}
""")

                operar(iq, par, direccion)

            time.sleep(0.5)

        except Exception as e:
            print(f"Error: {e}")
            time.sleep(2)


if __name__ == "__main__":
    run()
