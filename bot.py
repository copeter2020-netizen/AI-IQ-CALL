import time
from datetime import datetime
import pandas as pd
from iqoptionapi.stable_api import IQ_Option

# =========================
# CONFIG
# =========================
EMAIL = "TU_EMAIL"
PASSWORD = "TU_PASSWORD"
MONTO = 6

PARES = [
    "EURUSD-OTC",
    "USDCHF-OTC",
    "GBPUSD-OTC",
    "USDJPY-OTC"
]

# =========================
# CONEXIÓN
# =========================
API = IQ_Option(EMAIL, PASSWORD)
API.connect()

API.change_balance("PRACTICE")
print("✅ BOT CONECTADO A DEMO")

# =========================
# UTILIDADES
# =========================
def body(v):
    return abs(v["close"] - v["open"])

def rango(v):
    return v["max"] - v["min"]

def es_alcista(v):
    return v["close"] > v["open"]

def es_bajista(v):
    return v["close"] < v["open"]

# =========================
# AGOTAMIENTO
# =========================
def agotamiento(v):
    if rango(v) == 0:
        return None

    cuerpo = body(v)
    rango_total = rango(v)

    mecha_sup = v["max"] - max(v["open"], v["close"])
    mecha_inf = min(v["open"], v["close"]) - v["min"]

    # CALL
    if (
        es_bajista(v) and
        cuerpo < rango_total * 0.4 and
        mecha_inf > cuerpo * 2
    ):
        return "call"

    # PUT
    if (
        es_alcista(v) and
        cuerpo < rango_total * 0.4 and
        mecha_sup > cuerpo * 2
    ):
        return "put"

    return None

# =========================
# CAMBIO TENDENCIA
# =========================
def cambio_tendencia(v, tipo):

    if rango(v) == 0:
        return False

    cuerpo = body(v)
    rango_total = rango(v)

    if cuerpo < rango_total * 0.6:
        return False

    if tipo == "call":
        return es_alcista(v)

    if tipo == "put":
        return es_bajista(v)

    return False

# =========================
# OBTENER VELAS
# =========================
def obtener_velas(par):
    velas = API.get_candles(par, 60, 10, time.time())
    return pd.DataFrame(velas)

# =========================
# DETECTAR SEÑAL
# =========================
def detectar_entrada():

    for par in PARES:

        try:
            df = obtener_velas(par)

            v_prev = df.iloc[-2]
            v_actual = df.iloc[-1]

            tipo = agotamiento(v_prev)

            if not tipo:
                continue

            if not cambio_tendencia(v_actual, tipo):
                continue

            print(f"🎯 SEÑAL DETECTADA: {par} {tipo}")
            return par, tipo

        except Exception as e:
            print(f"⚠️ Error en {par}: {e}")

    return None

# =========================
# ESPERAR SEGUNDO 58
# =========================
def esperar_segundo_58():
    while True:
        now = datetime.now()
        if now.second >= 58:
            break
        time.sleep(0.2)

# =========================
# EJECUTAR OPERACIÓN
# =========================
def ejecutar_operacion(par, direccion):

    print(f"⏳ Esperando ejecución en {par}...")

    esperar_segundo_58()

    print(f"🚀 EJECUTANDO {direccion.upper()} en {par}")

    try:
        status, order_id = API.buy(MONTO, par, direccion, 1)

        if status:
            print(f"✅ OPERACIÓN EJECUTADA ID: {order_id}")
        else:
            print("❌ ERROR AL EJECUTAR")

    except Exception as e:
        print(f"❌ ERROR: {e}")

# =========================
# LOOP PRINCIPAL
# =========================
print("🤖 BOT INICIADO...")

while True:
    try:
        senal = detectar_entrada()

        if senal:
            par, direccion = senal

            ejecutar_operacion(par, direccion)

            # evitar múltiples entradas
            time.sleep(60)

        time.sleep(1)

    except Exception as e:
        print(f"❌ ERROR GENERAL: {e}")
        time.sleep(5)
