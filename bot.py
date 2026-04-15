import time
import os
import requests
import sys
from iqoptionapi.stable_api import IQ_Option

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)

from estrategia import detectar_entrada_oculta

EMAIL = os.getenv("IQ_EMAIL")
PASSWORD = os.getenv("IQ_PASSWORD")
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

MONTO = 50
CUENTA = "PRACTICE"

ultima_entrada = 0
bot_activo = True
update_id = None


# =========================
# TELEGRAM (ANTI-ERROR)
# =========================
def enviar_telegram(msg):
    if not TOKEN or not CHAT_ID:
        return

    try:
        requests.post(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            data={"chat_id": CHAT_ID, "text": msg},
            timeout=10  # 🔥 aumentamos timeout
        )
    except:
        pass  # 🔥 NO mostrar error


def verificar_comandos():
    global bot_activo, update_id

    if not TOKEN:
        return

    try:
        url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
        params = {"timeout": 5, "offset": update_id}

        res = requests.get(url, params=params, timeout=10).json()

        if "result" not in res:
            return

        for update in res["result"]:
            update_id = update["update_id"] + 1

            if "message" not in update:
                continue

            msg = update["message"].get("text", "")

            if msg == "/startbot":
                bot_activo = True
                enviar_telegram("🟢 BOT ACTIVADO")

            elif msg == "/stopbot":
                bot_activo = False
                enviar_telegram("🔴 BOT DETENIDO")

    except:
        pass  # 🔥 silenciar errores


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
                iq.get_all_ACTIVES_OPCODE()
                time.sleep(2)

                log("✅ BOT CONECTADO DEMO")
                return iq

        except Exception as e:
            print(f"Error conexión: {e}")  # 🔥 solo consola

        time.sleep(5)


# =========================
# RECONEXIÓN
# =========================
def asegurar_conexion(iq):
    try:
        if not iq.check_connect():
            print("Reconectando...")
            return conectar()
        return iq
    except:
        return conectar()


# =========================
# PARES ESTABLES
# =========================
PARES = [
    "EURUSD-OTC",
    "GBPUSD-OTC",
    "USDJPY-OTC",
    "USDCHF-OTC",
    "EURJPY-OTC",
    "GBPJPY-OTC"
]


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
# OPERAR INMEDIATO
# =========================
def operar(iq, par, direccion):
    global ultima_entrada

    if time.time() - ultima_entrada < 5:
        return False

    try:
        iq.subscribe_strike_list(par, 1)
        time.sleep(0.2)

        status, _ = iq.buy_digital_spot(par, MONTO, direccion, 1)

        iq.unsubscribe_strike_list(par, 1)

        if status:
            log(f"""🚀 OPERACIÓN

{par} {direccion.upper()}
Expiración 1M
""")
            ultima_entrada = time.time()
            return True
        else:
            print("❌ No ejecutó la orden")
            return False

    except Exception as e:
        try:
            iq.unsubscribe_strike_list(par, 1)
        except:
            pass

        print(f"Error operación: {e}")
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

                log(f"""🎯 SEÑAL

{par} {direccion}
Score: {score}
""")

                operar(iq, par, direccion)

            time.sleep(0.2)

        except Exception as e:
            print(f"Error general: {e}")  # 🔥 sin spam telegram
            time.sleep(2)


if __name__ == "__main__":
    run()
