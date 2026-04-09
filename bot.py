import time
import os
import requests
import sys
from iqoptionapi.stable_api import IQ_Option

# =========================
# PATH
# =========================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)

from estrategia import detectar_entrada_oculta


# =========================
# VARIABLES DE ENTORNO
# =========================
EMAIL = os.getenv("IQ_EMAIL")
PASSWORD = os.getenv("IQ_PASSWORD")

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

MONTO = float(os.getenv("MONTO", 5))
CUENTA = os.getenv("CUENTA", "PRACTICE")

# SOLO OTC (ESTABLE)
PARES = [
    "EURUSD-OTC",
    "EURJPY-OTC",
    "EURGBP-OTC",
    "EURCHF-OTC",
    "EURAUD-OTC",
    "EURCAD-OTC",
    "GBPUSD-OTC",
    "GBPJPY-OTC",
    "GBPAUD-OTC",
    "GBPCAD-OTC",
    "GBPCHF-OTC",
    "USDJPY-OTC",
    "USDCHF-OTC",
    "USDCAD-OTC",
    "AUDUSD-OTC",
    "AUDJPY-OTC",
    "AUDCAD-OTC",
    "AUDCHF-OTC",
    "NZDJPY-OTC",
    "NZDCAD-OTC",
    "CADJPY-OTC",
    "CHFJPY-OTC", 
    "USDNOK-OTC",
    "USDSEK-OTC",
    "USDTRY-OTC",
    "USDZAR-OTC",
    "BTCUSD-OTC",
    "ETHUSD-OTC",
    "LTCUSD-OTC" 
]


# =========================
# TELEGRAM
# =========================
def enviar_mensaje(texto):
    if not TOKEN or not CHAT_ID:
        return

    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        requests.post(url, data={
            "chat_id": CHAT_ID,
            "text": texto
        }, timeout=5)
    except Exception as e:
        print("Error Telegram:", e)


# =========================
# CONEXIÓN SEGURA
# =========================
def conectar():
    while True:
        try:
            iq = IQ_Option(EMAIL, PASSWORD)
            iq.connect()

            if iq.check_connect():
                iq.change_balance(CUENTA)

                print("✅ CONECTADO A IQ OPTION")
                enviar_mensaje("✅ BOT CONECTADO")

                return iq

            else:
                print("❌ No conecta")

        except Exception as e:
            print("Error conexión:", e)

        time.sleep(5)


# =========================
# ESPERAR VELA
# =========================
def esperar_cierre():
    while True:
        now = time.time()

        if int(now) % 60 == 59:
            return

        time.sleep(0.05)


# =========================
# OBTENER VELAS (ANTI ERROR)
# =========================
def obtener_velas(iq, par):
    try:
        velas = iq.get_candles(par, 60, 60, time.time())

        if not velas or len(velas) < 30:
            return []

        return [{
            "open": v["open"],
            "close": v["close"],
            "max": v["max"],
            "min": v["min"]
        } for v in velas]

    except Exception as e:
        print(f"Error velas {par}:", e)
        return []


# =========================
# VALIDAR ACTIVO OTC
# =========================
def par_disponible(iq, par):
    try:
        activos = iq.get_all_open_time()

        return activos["digital"][par]["open"]

    except Exception:
        return False


# =========================
# OPERAR DIGITAL OTC
# =========================
def operar(iq, par, direccion):

    if not par_disponible(iq, par):
        print(f"❌ {par} cerrado")
        return False

    esperar_cierre()

    try:
        status, order_id = iq.buy_digital_spot(par, MONTO, direccion, 5)

        if status:
            print(f"🚀 OPERANDO {par} {direccion}")

            enviar_mensaje(f"""
🚀 ENTRADA EJECUTADA

Par: {par}
Dirección: {direccion.upper()}
Expiración: 5 MIN
Monto: ${MONTO}
""")
            return True
        else:
            print(f"❌ Fallo ejecución {par}")
            return False

    except Exception as e:
        print("Error al operar:", e)
        return False


# =========================
# MAIN LOOP
# =========================
def run():

    iq = conectar()
    ultima_operacion = 0

    while True:
        try:
            # evitar sobrecarga Railway
            if time.time() - ultima_operacion < 60:
                time.sleep(0.5)
                continue

            data = {}

            # obtener datos seguros
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

                print(f"🎯 {par} {direccion} | Score: {score}")

                ejecutado = operar(iq, par, direccion)

                if ejecutado:
                    ultima_operacion = time.time()
                    time.sleep(300)

            else:
                time.sleep(0.5)

        except Exception as e:
            print("Error general:", e)

            # 🔥 RECONEXIÓN AUTOMÁTICA (CLAVE)
            iq = conectar()

            time.sleep(5)


# =========================
# ENTRYPOINT
# =========================
if __name__ == "__main__":
    run()
