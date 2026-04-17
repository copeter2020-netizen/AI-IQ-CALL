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

MONTO = 50
CUENTA = "PRACTICE"

ultima_entrada = 0
update_id = None

# =========================
# CONFIG PANEL
# =========================
config = {
    "tipo": "digital",
    "par": "EURUSD-OTC",
    "exp": 1,
    "monto": 50,
    "activo": True
}

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
# PANEL BOTONES
# =========================
def enviar_menu():
    keyboard = {
        "inline_keyboard": [
            [{"text": "📊 Tipo", "callback_data": "tipo"}],
            [{"text": "💱 Par", "callback_data": "par"}],
            [{"text": "⏱ Expiración", "callback_data": "exp"}],
            [{"text": "💰 Monto", "callback_data": "monto"}],
            [{"text": "🟢 Activar / 🔴 Detener", "callback_data": "control"}],
        ]
    }

    requests.post(
        f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        json={"chat_id": CHAT_ID, "text": "🎛 PANEL", "reply_markup": keyboard}
    )


def menu_tipo():
    keyboard = {
        "inline_keyboard": [
            [{"text": "DIGITAL", "callback_data": "tipo_digital"}],
            [{"text": "BINARIO", "callback_data": "tipo_binario"}],
        ]
    }

    requests.post(
        f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        json={"chat_id": CHAT_ID, "text": "Tipo:", "reply_markup": keyboard}
    )


def menu_pares():
    keyboard = {
        "inline_keyboard": [
            [{"text": "EURUSD", "callback_data": "par_EURUSD-OTC"}],
            [{"text": "GBPUSD", "callback_data": "par_GBPUSD-OTC"}],
            [{"text": "EURJPY", "callback_data": "par_EURJPY-OTC"}],
            [{"text": "USDCHF", "callback_data": "par_USDCHF-OTC"}],
            [{"text": "GBPJPY", "callback_data": "par_GBPJPY-OTC"}],
            [{"text": "USDZAR", "callback_data": "par_USDZAR-OTC"}],
        ]
    }

    requests.post(
        f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        json={"chat_id": CHAT_ID, "text": "Par:", "reply_markup": keyboard}
    )


def menu_exp():
    keyboard = {
        "inline_keyboard": [
            [{"text": "1M", "callback_data": "exp_1"}],
            [{"text": "2M", "callback_data": "exp_2"}],
            [{"text": "3M", "callback_data": "exp_3"}],
            [{"text": "4M", "callback_data": "exp_4"}],
            [{"text": "5M", "callback_data": "exp_5"}],
        ]
    }

    requests.post(
        f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        json={"chat_id": CHAT_ID, "text": "Exp:", "reply_markup": keyboard}
    )


def menu_monto():
    keyboard = {
        "inline_keyboard": [
            [{"text": "$10", "callback_data": "monto_10"}],
            [{"text": "$50", "callback_data": "monto_50"}],
            [{"text": "$100", "callback_data": "monto_100"}],
        ]
    }

    requests.post(
        f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        json={"chat_id": CHAT_ID, "text": "Monto:", "reply_markup": keyboard}
    )


def verificar_botones():
    global update_id

    try:
        res = requests.get(
            f"https://api.telegram.org/bot{TOKEN}/getUpdates",
            params={"offset": update_id},
            timeout=3
        ).json()

        for u in res.get("result", []):
            update_id = u["update_id"] + 1

            if "callback_query" not in u:
                continue

            data = u["callback_query"]["data"]

            if data == "tipo":
                menu_tipo()

            elif data == "par":
                menu_pares()

            elif data == "exp":
                menu_exp()

            elif data == "monto":
                menu_monto()

            elif data == "control":
                config["activo"] = not config["activo"]
                log(f"BOT {'ACTIVO' if config['activo'] else 'DETENIDO'}")

            elif "tipo_" in data:
                config["tipo"] = data.split("_")[1]

            elif "par_" in data:
                config["par"] = data.split("_")[1]

            elif "exp_" in data:
                config["exp"] = int(data.split("_")[1])

            elif "monto_" in data:
                config["monto"] = int(data.split("_")[1])

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
                iq.change_balance(CUENTA)
                log("✅ CONECTADO")
                return iq
        except:
            pass
        time.sleep(5)


# =========================
# VELAS
# =========================
def obtener_velas(iq, par):
    try:
        velas = iq.get_candles(par, 60, 30, time.time())
        return velas
    except:
        return None


# =========================
# OPERAR
# =========================
def operar(iq, direccion):
    global ultima_entrada

    if time.time() - ultima_entrada < 20:
        return

    try:
        iq.subscribe_strike_list(config["par"], config["exp"])
        time.sleep(1)

        status, _ = iq.buy_digital_spot(
            config["par"],
            config["monto"],
            direccion,
            config["exp"]
        )

        iq.unsubscribe_strike_list(config["par"], config["exp"])

        if status:
            log(f"🚀 {config['par']} {direccion.upper()}")

    except Exception as e:
        log(f"Error: {e}")


# =========================
# MAIN
# =========================
def run():
    iq = conectar()
    enviar_menu()

    while True:
        verificar_botones()

        if not config["activo"]:
            time.sleep(1)
            continue

        data = {}

        velas = obtener_velas(iq, config["par"])
        if velas:
            data[config["par"]] = velas

        señal = detectar_entrada_oculta(data)

        if señal:
            _, direccion, _ = señal
            operar(iq, direccion)

        time.sleep(0.5)


if __name__ == "__main__":
    run()
