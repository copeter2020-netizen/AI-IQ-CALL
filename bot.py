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

MONTO = 5050
CUENTA = "PRACTICE"

ultima_entrada = 0
bot_activo = False
update_id = None

par_seleccionado = None


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


def enviar_panel():
    teclado = {
        "keyboard": [
            ["💱 EURUSD", "💱 GBPUSD"],
            ["💱 EURJPY", "💱 USDCHF"],
            ["💱 GBPJPY", "💱 USDZAR"],
            ["💰 MONTO"],
            ["▶️ ACTIVAR", "⛔ DETENER"]
        ],
        "resize_keyboard": True
    }

    requests.post(
        f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        json={
            "chat_id": CHAT_ID,
            "text": "📊 PANEL DE CONTROL",
            "reply_markup": teclado
        }
    )


def verificar_comandos():
    global bot_activo, update_id, MONTO, par_seleccionado

    try:
        url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
        params = {"timeout": 1, "offset": update_id}

        res = requests.get(url, params=params, timeout=5).json()

        if "result" not in res:
            return

        for update in res["result"]:
            update_id = update["update_id"] + 1

            if "message" not in update:
                continue

            msg = update["message"].get("text", "").upper()

            if msg == "/START":
                enviar_panel()

            elif "EURUSD" in msg:
                par_seleccionado = "EURUSD-OTC"
                enviar_telegram("✅ Analizando EURUSD...")

            elif "GBPUSD" in msg:
                par_seleccionado = "GBPUSD-OTC"
                enviar_telegram("✅ Analizando GBPUSD...")

            elif "EURJPY" in msg:
                par_seleccionado = "EURJPY-OTC"
                enviar_telegram("✅ Analizando EURJPY...")

            elif "USDCHF" in msg:
                par_seleccionado = "USDCHF-OTC"
                enviar_telegram("✅ Analizando USDCHF...")

            elif "GBPJPY" in msg:
                par_seleccionado = "GBPJPY-OTC"
                enviar_telegram("✅ Analizando GBPJPY...")

            elif "USDZAR" in msg:
                par_seleccionado = "USDZAR-OTC"
                enviar_telegram("✅ Analizando USDZAR...")

            elif msg.isdigit():
                MONTO = int(msg)
                enviar_telegram(f"💰 Monto: {MONTO}")

            elif "ACTIVAR" in msg:
                bot_activo = True
                enviar_telegram("🟢 BOT ACTIVADO")

            elif "DETENER" in msg:
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
# VELAS
# =========================
def obtener_velas(iq, par):
    try:
        velas = iq.get_candles(par, 60, 50, time.time())
        return velas
    except:
        return None


# =========================
# ESPERAR CIERRE VELA
# =========================
def esperar_cierre():
    actual = int(time.time() % 60)
    return actual >= 58


# =========================
# OPERAR
# =========================
def operar(iq, par, direccion):
    global ultima_entrada

    if time.time() - ultima_entrada < 10:
        return False

    try:
        status, order_id = iq.buy(MONTO, par, direccion, 1)

        if status:
            log(f"""🚀 OPERACIÓN

📊 {par}
📈 {direccion.upper()}
💰 {MONTO}
""")
            ultima_entrada = time.time()
            return True
        else:
            print("❌ No ejecutó")
            return False

    except Exception as e:
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
            iq = asegurar_conexion(iq)

            if not bot_activo or not par_seleccionado:
                time.sleep(1)
                continue

            velas = obtener_velas(iq, par_seleccionado)

            if not velas or len(velas) < 20:
                continue

            # 🔥 ANALIZA ESTRUCTURA TODO EL TIEMPO
            estructura = detectar_entrada_oculta({par_seleccionado: velas})

            # 🔥 SOLO CONFIRMA EN CIERRE DE VELA
            if estructura and esperar_cierre():

                par, direccion, score = estructura

                log(f"""📊 CONFIRMACIÓN

Par: {par}
Dirección: {direccion}
Score: {score}
""")

                operar(iq, par, direccion)

            time.sleep(0.3)

        except Exception as e:
            print(f"Error general: {e}")
            time.sleep(2)


if __name__ == "__main__":
    run()
