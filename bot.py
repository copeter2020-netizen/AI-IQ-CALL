import time
import os
import requests
import sys
from iqoptionapi.stable_api import IQ_Option
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)

try:
    from estrategia import detectar_entrada_oculta, niveles
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
    "EURJPY-OTC",
    "EURGBP-OTC",
    "GBPJPY-OTC",
    "USDCHF-OTC"
]

ultimo_update_id = None
bot_activo = False


# =========================
# TELEGRAM
# =========================
def enviar_mensaje(texto):
    try:
        requests.post(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            data={
                "chat_id": CHAT_ID,
                "text": texto
            },
            timeout=5
        )
    except Exception as e:
        print("❌ Error Telegram:", e)


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
# CONEXIÓN
# =========================
def conectar():
    while True:
        try:
            iq = IQ_Option(EMAIL, PASSWORD)
            iq.connect()

            if iq.check_connect():
                iq.change_balance(CUENTA)
                print("✅ CONECTADO")
                enviar_mensaje("🤖 BOT CONECTADO A IQ OPTION")
                return iq

        except Exception as e:
            print("Error conexión:", e)

        time.sleep(5)


# =========================
# DATOS
# =========================
def obtener_velas(iq, par):
    try:
        velas = iq.get_candles(par, 60, 200, time.time())

        return [{
            "open": v["open"],
            "close": v["close"],
            "max": v["max"],
            "min": v["min"]
        } for v in velas]

    except:
        return None


def precio_actual(iq, par):
    try:
        velas = iq.get_candles(par, 60, 1, time.time())
        return velas[-1]["close"]
    except:
        return None


# =========================
# ENTRADA INTELIGENTE
# =========================
def esperar_toque_y_operar(iq, par, direccion, score):

    inicio = time.time()

    while time.time() - inicio < 300:

        velas = obtener_velas(iq, par)
        if not velas:
            continue

        df = pd.DataFrame(velas)
        soporte, resistencia = niveles(df)
        precio = precio_actual(iq, par)

        if precio is None:
            continue

        if direccion == "put" and precio >= resistencia:
            enviar_mensaje(f"🎯 ENTRADA EN RESISTENCIA\n{par} PUT")
            status, _ = iq.buy_digital_spot(par, MONTO, direccion, 5)
            return status

        if direccion == "call" and precio <= soporte:
            enviar_mensaje(f"🎯 ENTRADA EN SOPORTE\n{par} CALL")
            status, _ = iq.buy_digital_spot(par, MONTO, direccion, 5)
            return status

        time.sleep(1)

    enviar_mensaje("⏱ No tocó zona, no se operó")
    return False


# =========================
# MAIN
# =========================
def run():

    if detectar_entrada_oculta is None:
        print("❌ Falta estrategia.py")
        return

    iq = conectar()
    ultima_operacion = 0

    while True:
        try:
            leer_comandos()

            if not bot_activo:
                time.sleep(1)
                continue

            if time.time() - ultima_operacion < 30:
                time.sleep(1)
                continue

            data = {}

            for par in PARES:
                velas = obtener_velas(iq, par)
                if velas:
                    data[par] = velas
                time.sleep(0.2)

            if not data:
                continue

            señal = detectar_entrada_oculta(data)

            if señal:
                par, direccion, score = señal

                mensaje = f"""🚨 SEÑAL DETECTADA

Par: {par}
Dirección: {direccion.upper()}
Expiración: 5 MIN
Score: {score}
"""
                enviar_mensaje(mensaje)

                if esperar_toque_y_operar(iq, par, direccion, score):
                    ultima_operacion = time.time()
                    time.sleep(300)

            else:
                time.sleep(1)

        except Exception as e:
            print("❌ Error:", e)
            iq = conectar()


if __name__ == "__main__":
    run()
