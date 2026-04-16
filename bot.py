import time
import os
import requests
import sys
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

if not all([EMAIL, PASSWORD, TOKEN, CHAT_ID]):
    raise Exception("❌ Faltan variables de entorno")

MONTO = 500
CUENTA = "PRACTICE"

ultima_entrada = 0
bot_activo = True
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


def verificar_comandos():
    global bot_activo, update_id

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

            if msg == "/startbot":
                bot_activo = True
                log("🟢 BOT ACTIVADO")

            elif msg == "/stopbot":
                bot_activo = False
                log("🔴 BOT DETENIDO")

    except Exception as e:
        print(f"Error Telegram: {e}")


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
                iq.get_all_ACTIVES_OPCODE()
                time.sleep(2)

                log("✅ BOT CONECTADO DEMO")
                return iq

        except Exception as e:
            log(f"Error conexión: {e}")

        time.sleep(5)


def asegurar_conexion(iq):
    try:
        if not iq.check_connect():
            log("🔄 Reconectando...")
            return conectar()
        return iq
    except:
        return conectar()


# =========================
# PARES
# =========================
PARES = [
    "EURUSD-OTC",
    "GBPUSD-OTC",
    "USDZAR-OTC",
    "EURJPY-OTC",
    "GBPJPY-OTC",
    "USDCHF-OTC"
]


# =========================
# TIMING
# =========================
def esperar_entrada():
    while True:
        if int(time.time() % 60) >= 58:
            break
        time.sleep(0.01)


# =========================
# VELAS
# =========================
def obtener_velas(iq, par):
    try:
        velas = iq.get_candles(par, 60, 30, time.time())

        if not velas or len(velas) < 10:
            return None

        return [{
            "open": v.get("open"),
            "close": v.get("close"),
            "max": v.get("max"),
            "min": v.get("min")
        } for v in velas]

    except Exception as e:
        print(f"Error velas {par}: {e}")
        return None


# =========================
# OPERAR
# =========================
def operar(iq, par, direccion):
    global ultima_entrada

    if time.time() - ultima_entrada < 30:
        return False

    log(f"⏳ Esperando entrada {par}")

    esperar_entrada()

    try:
        iq.subscribe_strike_list(par, 1)
        time.sleep(0.5)

        status, order_id = iq.buy_digital_spot(par, MONTO, direccion, 1)

        iq.unsubscribe_strike_list(par, 1)

        if status:
            log(f"""🚀 OPERACIÓN EJECUTADA

📊 {par}
📈 Dirección: {direccion.upper()}
⏱ Expiración: 1M
💰 Monto: {MONTO}
""")
            ultima_entrada = time.time()
            return True
        else:
            log("❌ No ejecutó la orden")
            return False

    except Exception as e:
        try:
            iq.unsubscribe_strike_list(par, 1)
        except:
            pass

        log(f"❌ Error operación: {e}")
        return False


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

            data = {}

            for par in PARES:
                velas = obtener_velas(iq, par)
                if velas:
                    data[par] = velas

            if not data:
                time.sleep(1)
                continue

            señal = detectar_entrada_oculta(data)

            if señal:
                par, direccion, score = señal

                log(f"""🎯 SEÑAL DETECTADA

📊 {par}
📈 {direccion}
⭐ Score: {score}
""")

                operar(iq, par, direccion)

            time.sleep(0.2)

        except Exception as e:
            log(f"❌ Error general: {e}")
            time.sleep(2)


if __name__ == "__main__":
    run()
