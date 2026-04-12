import time
import os
import requests
import sys
from iqoptionapi.stable_api import IQ_Option

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)

try:
    from estrategia import detectar_entrada_oculta
except Exception as e:
    print("❌ Error importando estrategia:", e)
    detectar_entrada_oculta = None


EMAIL = os.getenv("IQ_EMAIL")
PASSWORD = os.getenv("IQ_PASSWORD")

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

MONTO = 10000
CUENTA = "PRACTICE"

PARES = [
    "EURUSD-OTC",
    "GBPUSD-OTC",
    "USDJPY-OTC",
    "EURJPY-OTC",
    "EURGBP-OTC",
    "GBPJPY-OTC",
    "USDCHF-OTC"
]

ultima_entrada = 0
ultimo_update_id = None
bot_activo = True


# =========================
# TELEGRAM
# =========================
def enviar_mensaje(texto):
    try:
        requests.post(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            data={"chat_id": CHAT_ID, "text": texto},
            timeout=5
        )
    except:
        pass


def leer_comandos():
    global ultimo_update_id, bot_activo

    try:
        url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
        params = {"timeout": 1, "offset": ultimo_update_id}
        res = requests.get(url, params=params, timeout=5).json()

        for update in res.get("result", []):
            ultimo_update_id = update["update_id"] + 1

            mensaje = update.get("message", {}).get("text", "")

            if mensaje == "/startbot":
                bot_activo = True
                enviar_mensaje("✅ BOT ACTIVADO")

            elif mensaje == "/stopbot":
                bot_activo = False
                enviar_mensaje("⛔ BOT DETENIDO")

    except:
        pass


# =========================
# ⏱ ESPERA PRECISA
# =========================
def esperar_entrada_precisa():
    while True:
        ahora = time.time()
        restante = 60 - (ahora % 60)

        if restante <= 0.03:
            break

        time.sleep(0.005)

    time.sleep(1.1)


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
                enviar_mensaje("🤖 BOT CONECTADO")
                return iq
        except:
            pass

        time.sleep(5)


# =========================
# DATOS
# =========================
def obtener_velas(iq, par):
    try:
        velas = iq.get_candles(par, 60, 50, time.time())

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
def operar(iq, par, direccion, score):
    global ultima_entrada

    if time.time() - ultima_entrada < 10:
        return

    enviar_mensaje("⏱ Preparando entrada...")

    esperar_entrada_precisa()

    try:
        status, _ = iq.buy_digital_spot(par, MONTO, direccion, 1)

        if status:
            enviar_mensaje(f"""🚀 OPERACIÓN EJECUTADA

Par: {par}
Dirección: {direccion.upper()}
""")
            ultima_entrada = time.time()
        else:
            enviar_mensaje("❌ No se pudo ejecutar")

    except Exception as e:
        print("Error:", e)


# =========================
# MAIN
# =========================
def run():

    if detectar_entrada_oculta is None:
        return

    iq = conectar()

    while True:
        try:
            # 🔥 Leer comandos SIEMPRE
            leer_comandos()

            # ⛔ Si está detenido, no analiza ni opera
            if not bot_activo:
                time.sleep(1)
                continue

            data = {}

            for par in PARES:
                velas = obtener_velas(iq, par)

                if velas:
                    data[par] = velas

            señal = detectar_entrada_oculta(data)

            if señal:
                par, direccion, score = señal

                enviar_mensaje(f"""🎯 SEÑAL

Par: {par}
Dirección: {direccion.upper()}
""")

                operar(iq, par, direccion, score)

            time.sleep(0.3)

        except Exception as e:
            print("Error:", e)
            iq = conectar()


if __name__ == "__main__":
    run()
