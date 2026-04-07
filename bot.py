import time
import os
import requests
import sys
from iqoptionapi.stable_api import IQ_Option

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)

try:
    from estrategia import detectar_entrada_oculta
except:
    detectar_entrada_oculta = None


EMAIL = os.getenv("IQ_EMAIL")
PASSWORD = os.getenv("IQ_PASSWORD")

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

MONTO = 3600
CUENTA = "PRACTICE"

PARES = [
    "EURUSD-OTC",
    "EURJPY-OTC",
    "EURGBP-OTC",
    "USDCHF-OTC",
    "GBPUSD-OTC",
    "AUDUSD-OTC",
    "USDCAD-OTC",
    "NZDUSD-OTC",
    "USDJPY-OTC",
    "GBPJPY-OTC",
    "EURCHF-OTC",
    "AUDJPY-OTC",
    "CADJPY-OTC",
    "CHFJPY-OTC",
    "EURAUD-OTC",
    "EURNZD-OTC",
    "GBPAUD-OTC",
    "GBPNZD-OTC",
    "AUDCAD-OTC",
    "AUDCHF-OTC",
    "AUDNZD-OTC",
    "CADCHF-OTC",
    "NZDJPY-OTC",
    "NZDCHF-OTC",
    "NZDCAD-OTC",
    "USDNOK-OTC",
    "USDSEK-OTC",
    "USDDKK-OTC",
    "USDZAR-OTC",
    "USDSGD-OTC",
    "USDHKD-OTC",
    "USDTRY-OTC",
    "USDTHB-OTC",
    "USDMXN-OTC",
    "USDPLN-OTC",
    "USDINR-OTC",
    "USDPHP-OTC",
    "EURTRY-OTC",
    "EURZAR-OTC",
    "EURSGD-OTC",
    "GBPCHF-OTC",
    "GBPCHF-OTC",
    "CHFSGD-OTC",
    "AUDSGD-OTC",
    "CADSGD-OTC",
    "EURNOK-OTC",
    "EURSEK-OTC"
]


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
                return iq
        except:
            pass

        time.sleep(5)


# =========================
# 🔥 ESPERAR CIERRE REAL M5
# =========================
def esperar_cierre_m5():
    while True:
        t = time.localtime()

        if t.tm_min % 5 == 0 and t.tm_sec == 0:
            return

        time.sleep(0.2)


# =========================
# VELAS M5
# =========================
def obtener_velas(iq, par):
    try:
        velas = iq.get_candles(par, 300, 40, time.time())

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
# OPERAR M5
# =========================
def operar(iq, par, direccion):
    try:
        esperar_cierre_m5()

        check, _ = iq.buy(MONTO, par, direccion, 2)

        if check:
            print(f"🚀 ENTRADA {par} {direccion.upper()}")

            enviar_mensaje(
                f"🚀 ENTRADA M5\nPar: {par}\nDirección: {direccion.upper()}\nMonto: ${MONTO}"
            )

    except:
        pass


# =========================
# MAIN
# =========================
def run():

    if detectar_entrada_oculta is None:
        print("❌ Falta estrategia.py")
        return

    iq = conectar()

    while True:
        try:
            data = {}

            for par in PARES:
                velas = obtener_velas(iq, par)

                if velas is not None:
                    data[par] = velas

            if not data:
                time.sleep(1)
                continue

            señal = detectar_entrada_oculta(data)

            if señal:
                par, direccion, score = señal

                print(f"🎯 Señal {par} {direccion.upper()} Score:{score}")

                operar(iq, par, direccion)

                time.sleep(300)  # esperar siguiente vela

            else:
                time.sleep(1)

        except:
            time.sleep(2)


if __name__ == "__main__":
    run()
