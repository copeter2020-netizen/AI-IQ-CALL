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

MONTO = 5
CUENTA = "PRACTICE"

PARES = [
    "EURUSD-OTC","EURJPY-OTC","EURGBP-OTC","EURCHF-OTC","EURAUD-OTC",
    "EURCAD-OTC","GBPUSD-OTC","GBPJPY-OTC","GBPAUD-OTC","GBPCAD-OTC",
    "GBPCHF-OTC","USDJPY-OTC","USDCHF-OTC","USDCAD-OTC","AUDUSD-OTC",
    "AUDJPY-OTC","AUDCAD-OTC","AUDCHF-OTC","NZDJPY-OTC","NZDCAD-OTC",
    "CADJPY-OTC","CHFJPY-OTC","USDNOK-OTC","USDSEK-OTC","USDTRY-OTC",
    "USDZAR-OTC","BTCUSD-OTC","ETHUSD-OTC","LTCUSD-OTC"
]


# =========================
# TELEGRAM
# =========================
def enviar_mensaje(texto):
    if not TOKEN or not CHAT_ID:
        return

    try:
        requests.post(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            data={"chat_id": CHAT_ID, "text": texto},
            timeout=5
        )
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
                enviar_mensaje("✅ BOT CONECTADO")
                return iq

        except:
            pass

        time.sleep(5)


# =========================
# VALIDAR PAR OTC
# =========================
def par_abierto(iq, par):
    try:
        info = iq.get_all_open_time()

        if "digital" not in info:
            return False

        if par not in info["digital"]:
            return False

        return info["digital"][par]["open"]

    except:
        return False


# =========================
# TIEMPO
# =========================
def esperar_cierre():
    while True:
        t = time.time()

        if int(t) % 60 == 59:
            return

        time.sleep(0.01)


# =========================
# DATOS
# =========================
def obtener_velas(iq, par):
    try:
        velas = iq.get_candles(par, 60, 50, time.time())

        if not velas or len(velas) < 30:
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
# OPERAR SIN UNDERLYING
# =========================
def operar(iq, par, direccion):

    if not par_abierto(iq, par):
        return False

    esperar_cierre()

    try:
        status, order_id = iq.buy_digital_spot(par, MONTO, direccion, 1)

        if status:
            print(f"🚀 {par} {direccion}")
            enviar_mensaje(f"🚀 {par} {direccion.upper()}")
            return True

    except:
        # 🔥 reintento automático
        try:
            time.sleep(1)
            status, order_id = iq.buy_digital_spot(par, MONTO, direccion, 1)

            if status:
                print(f"🚀 {par} {direccion}")
                enviar_mensaje(f"🚀 {par} {direccion.upper()}")
                return True
        except:
            pass

    return False


# =========================
# MAIN
# =========================
def run():

    iq = conectar()
    ultima_operacion = 0

    while True:
        try:
            if time.time() - ultima_operacion < 60:
                time.sleep(0.3)
                continue

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

                print(f"🎯 {par} {direccion} Score:{score}")

                if operar(iq, par, direccion):
                    ultima_operacion = time.time()
                    time.sleep(60)

            else:
                time.sleep(0.3)

        except:
            # 🔥 reconexión automática
            iq = conectar()
            time.sleep(5)


if __name__ == "__main__":
    run()
