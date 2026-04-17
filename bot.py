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

MONTO = 50
TIEMPO = 1
PAR = "EURUSD-OTC"

bot_activo = False
ultima_entrada = 0
update_id = None


# =========================
# TELEGRAM
# =========================
def enviar_telegram(msg):
    try:
        requests.post(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            data={"chat_id": CHAT_ID, "text": msg},
            timeout=5
        )
    except:
        pass


def log(msg):
    print(msg)
    enviar_telegram(msg)


# =========================
# BOTONES / CONTROL
# =========================
def verificar_comandos():
    global bot_activo, update_id, PAR, MONTO, TIEMPO

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

            # CONTROL BOT
            if msg == "▶️ START":
                bot_activo = True
                log("🟢 BOT ACTIVADO")

            elif msg == "⏹ STOP":
                bot_activo = False
                log("🔴 BOT DETENIDO")

            # PARES
            elif msg in ["EURUSD", "GBPUSD", "EURJPY", "USDCHF", "GBPJPY", "USDZAR"]:
                PAR = msg + "-OTC"
                log(f"📊 Par seleccionado: {PAR}")

            # TIEMPO
            elif msg in ["1M", "2M", "3M", "4M", "5M"]:
                TIEMPO = int(msg.replace("M", ""))
                log(f"⏱ Tiempo: {TIEMPO}M")

            # MONTO MANUAL
            elif msg.isdigit():
                MONTO = int(msg)
                log(f"💰 Monto actualizado: {MONTO}")

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
                iq.change_balance("PRACTICE")
                iq.get_all_ACTIVES_OPCODE()

                log("✅ BOT CONECTADO")
                return iq

        except Exception as e:
            print(f"Error conexión: {e}")

        time.sleep(5)


def asegurar_conexion(iq):
    try:
        if not iq.check_connect():
            return conectar()
        return iq
    except:
        return conectar()


# =========================
# VELAS
# =========================
def obtener_velas(iq, par):
    try:
        velas = iq.get_candles(par, 60, 30, time.time())

        if not velas:
            return None

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

    if time.time() - ultima_entrada < 10:
        return False

    try:
        status, order_id = iq.buy(MONTO, par, direccion, TIEMPO)

        if status:
            log(f"""🚀 OPERACIÓN

📊 {par}
📈 {direccion.upper()}
⏱ {TIEMPO}M
💰 {MONTO}
ID: {order_id}
""")
            ultima_entrada = time.time()
        else:
            print("❌ No ejecutó")

    except Exception as e:
        print(f"Error operación: {e}")


# =========================
# MAIN
# =========================
def run():

    iq = conectar()

    while True:
        try:
            verificar_comandos()

            if not bot_activo:
                time.sleep(1)
                continue

            iq = asegurar_conexion(iq)

            velas = obtener_velas(iq, PAR)

            if not velas:
                continue

            señal = detectar_entrada_oculta({PAR: velas})

            if señal:
                _, direccion, score = señal

                log(f"""🎯 SEÑAL

{PAR}
{direccion}
Score: {score}
""")

                operar(iq, PAR, direccion)

            time.sleep(0.5)

        except Exception as e:
            print(f"Error: {e}")
            time.sleep(2)


if __name__ == "__main__":
    run()
