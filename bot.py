import time
import os
import sys
import pandas as pd
from iqoptionapi.stable_api import IQ_Option

# =========================
# IMPORTAR ESTRATEGIA
# =========================
try:
    from estrategia import detectar_entrada
except:
    print("❌ Falta estrategia.py")
    sys.exit()

# =========================
# CONFIG
# =========================
EMAIL = os.getenv("IQ_EMAIL")
PASSWORD = os.getenv("IQ_PASSWORD")

PARIDADES = [
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

MONTO = 1
TIEMPO = 4  # 4 minuto

# =========================
# CONEXIÓN
# =========================
Iq = IQ_Option(EMAIL, PASSWORD)
Iq.connect()

if not Iq.check_connect():
    print("❌ Error conectando")
    sys.exit()
else:
    print("✅ Conectado")

# =========================
# OBTENER DATOS
# =========================
def obtener_candles(par):
    try:
        candles = Iq.get_candles(par, 60, 50, time.time())
        df = pd.DataFrame(candles)
        df.rename(columns={
            "min": "min",
            "max": "max",
            "open": "open",
            "close": "close"
        }, inplace=True)
        return df
    except:
        return None

# =========================
# EJECUTAR TRADE
# =========================
def ejecutar_trade(par, direccion):
    try:
        status, id = Iq.buy(MONTO, par, direccion, TIEMPO)
        if status:
            print(f"🚀 ENTRADA {par} {direccion.upper()}")
    except:
        pass

# =========================
# LOOP PRINCIPAL
# =========================
while True:
    for par in PARIDADES:
        df = obtener_candles(par)

        if df is None:
            continue

        señal = detectar_entrada(df)

        if señal:
            print(f"📊 Señal {par} {señal.upper()}")
            ejecutar_trade(par, señal)

    time.sleep(10)
