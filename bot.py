import time
import os
import requests
from iqoptionapi.stable_api import IQ_Option
from estrategia import detectar_mejor_entrada

EMAIL = os.getenv("IQ_EMAIL")
PASSWORD = os.getenv("IQ_PASSWORD")

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

MONTO = 1000
CUENTA = "PRACTICE"

# 🔥 LISTA COMPLETA (IMÁGENES + ANTERIORES)
PARES = [

    # FOREX OTC
    "EURUSD-OTC","GBPUSD-OTC","USDJPY-OTC","USDCHF-OTC",
    "EURJPY-OTC","EURGBP-OTC","GBPJPY-OTC","AUDUSD-OTC",
    "USDCAD-OTC","NZDUSD-OTC","EURCAD-OTC","GBPCAD-OTC",
    "EURAUD-OTC","GBPAUD-OTC","AUDJPY-OTC","CHFJPY-OTC",
    "NZDJPY-OTC","AUDCAD-OTC","AUDCHF-OTC","CADJPY-OTC",
    "NZDCAD-OTC","NZDCHF-OTC","EURCHF-OTC","GBPNZD-OTC",
    "EURNZD-OTC","AUDNZD-OTC","USDZAR-OTC","USDSGD-OTC",
    "USDHKD-OTC","USDTRY-OTC","USDNOK-OTC","USDSEK-OTC",
    "USDMXN-OTC","USDPLN-OTC","USDHUF-OTC","USDCZK-OTC",

    # CRIPTOS / OTC
    "BTCUSD-OTC","ETHUSD-OTC","LTCUSD-OTC","XRPUSD-OTC",
    "ADAUSD-OTC","DOTUSD-OTC","SOLUSD-OTC","BNBUSD-OTC",

    # ACCIONES OTC (de tus imágenes)
    "AIG-OTC","Amazon-OTC","Apple-OTC","Tesla-OTC",
    "Google-OTC","Microsoft-OTC","Netflix-OTC",
    "Nvidia-OTC","Meta-OTC","Intel-OTC","AMD-OTC",

    # OTROS QUE SE VEN
    "Gold-OTC","Silver-OTC","Oil-OTC","NaturalGas-OTC",
    "Platinum-OTC","Palladium-OTC",

    # ÍNDICES / OTROS
    "SP500-OTC","NASDAQ-OTC","DOWJONES-OTC",

    # EXTRA (de listas visibles)
    "Alibaba-OTC","Baidu-OTC","Cisco-OTC","Oracle-OTC",
    "IBM-OTC","JPMorgan-OTC","Visa-OTC","Mastercard-OTC"
]

# =========================
def enviar(msg):
    try:
        if TOKEN and CHAT_ID:
            requests.post(
                f"https://api.telegram.org/bot{TOKEN}/sendMessage",
                data={"chat_id": CHAT_ID, "text": msg},
                timeout=5
            )
    except:
        pass

# =========================
def conectar():
    while True:
        try:
            iq = IQ_Option(EMAIL, PASSWORD)
            iq.connect()

            if iq.check_connect():
                iq.change_balance(CUENTA)
                print("BOT ACTIVADO")
                enviar("🤖 BOT ACTIVADO")
                return iq
        except:
            pass

        time.sleep(5)

# =========================
def velas(iq, par):
    try:
        data = iq.get_candles(par, 60, 60, time.time())

        return [{
            "open": v["open"],
            "close": v["close"],
            "max": v["max"],
            "min": v["min"]
        } for v in data]

    except:
        return []

# =========================
def operar(iq, par, direccion):
    check, _ = iq.buy(MONTO, par, direccion, 4)

    if check:
        print(f"SEÑAL → {par} {direccion}")
        enviar(f"🚀 {par} → {direccion.upper()}")

# =========================
def run():

    iq = conectar()

    while True:
        try:

            data = {}

            for par in PARES:
                data[par] = velas(iq, par)

            resultado = detectar_mejor_entrada(data)

            if resultado:
                par, direccion, score = resultado

                segundos = int(time.time()) % 60
                esperar = 60 - segundos

                if esperar > 0:
                    time.sleep(esperar)

                operar(iq, par, direccion)

                time.sleep(240)

            else:
                time.sleep(2)

        except:
            time.sleep(5)

# =========================
if __name__ == "__main__":
    run()
