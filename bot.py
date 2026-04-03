import time
import os
import requests
import numpy as np
from iqoptionapi.stable_api import IQ_Option

# =========================
# VARIABLES
# =========================
EMAIL = os.getenv("IQ_EMAIL")
PASSWORD = os.getenv("IQ_PASSWORD")

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

MONTO = 10
CUENTA = "PRACTICE"

PARES = [
    "EURUSD",
    "EURJPY",
    "EURGBP",
    "GBPUSD",
    "USDCHF"
]

ultima_operacion = 0


# =========================
# TELEGRAM
# =========================
def enviar_mensaje(texto):
    try:
        if not TOKEN or not CHAT_ID:
            print("⚠️ Telegram no configurado")
            return

        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

        requests.post(url, data={
            "chat_id": CHAT_ID,
            "text": texto
        }, timeout=5)

    except Exception as e:
        print("Error Telegram:", e)


# =========================
# CONEXIÓN
# =========================
def conectar():
    while True:
        try:
            iq = IQ_Option(EMAIL, PASSWORD)
            iq.connect()

            if iq.check_connect():
                print("✅ CONECTADO A IQ OPTION")
                iq.change_balance(CUENTA)
                return iq
            else:
                print("❌ Error credenciales")
                time.sleep(10)

        except Exception as e:
            print("Error conexión:", e)
            time.sleep(10)


# =========================
# VELAS
# =========================
def obtener_velas(iq, par):
    try:
        velas = iq.get_candles(par, 60, 100, time.time())

        return [{
            "open": v["open"],
            "close": v["close"],
            "max": v["max"],
            "min": v["min"]
        } for v in velas]

    except:
        return []


# =========================
# MERCADO OPERABLE
# =========================
def mercado_operable(velas):
    try:
        highs = np.array([v["max"] for v in velas])
        lows = np.array([v["min"] for v in velas])
        closes = np.array([v["close"] for v in velas])

        vol_actual = np.mean(highs[-5:] - lows[-5:])
        vol_pasada = np.mean(highs[-30:] - lows[-30:])
        rango = max(highs[-20:]) - min(lows[-20:])
        pendiente = abs(np.polyfit(range(20), closes[-20:], 1)[0])
        ruido = np.std(closes[-10:])

        if vol_actual < vol_pasada * 0.9:
            return False

        if rango < vol_actual * 2:
            return False

        if pendiente < 0.00001:
            return False

        if ruido > vol_actual:
            return False

        return True

    except:
        return False


# =========================
# ZONA PROHIBIDA
# =========================
def zona_prohibida(highs, lows, precio):
    maximo = max(highs[-30:])
    minimo = min(lows[-30:])
    rango = maximo - minimo

    if rango == 0:
        return True

    pos = (precio - minimo) / rango

    return pos > 0.85 or pos < 0.15


# =========================
# SCORE PAR
# =========================
def score_par(velas):
    highs = np.array([v["max"] for v in velas])
    lows = np.array([v["min"] for v in velas])
    closes = np.array([v["close"] for v in velas])

    volatilidad = np.mean(highs[-10:] - lows[-10:])
    tendencia = abs(np.polyfit(range(10), closes[-10:], 1)[0])
    ruido = np.std(closes[-10:])

    return (volatilidad * 2) + (tendencia * 5) - ruido


# =========================
# ESTRATEGIA FINAL
# =========================
def detectar_entrada(data):
    global ultima_operacion

    ahora = time.time()

    if ahora - ultima_operacion < 900:
        return None

    candidatos = []

    for par, velas in data.items():

        if len(velas) < 80:
            continue

        if not mercado_operable(velas):
            continue

        calidad = score_par(velas)
        candidatos.append((par, velas, calidad))

    if not candidatos:
        print("💤 Mercado no óptimo...")
        return None

    candidatos.sort(key=lambda x: x[2], reverse=True)

    par, velas, _ = candidatos[0]

    highs = [v["max"] for v in velas]
    lows = [v["min"] for v in velas]

    v1 = velas[-1]
    v2 = velas[-2]

    o1, c1, h1, l1 = v1["open"], v1["close"], v1["max"], v1["min"]
    o2, c2, h2, l2 = v2["open"], v2["close"], v2["max"], v2["min"]

    if zona_prohibida(highs, lows, c1):
        return None

    max_prev = max(highs[-20:-2])
    min_prev = min(lows[-20:-2])

    if h2 > max_prev and c2 < max_prev:
        direccion = "put"
    elif l2 < min_prev and c2 > min_prev:
        direccion = "call"
    else:
        return None

    if direccion == "put" and c1 >= c2:
        return None
    if direccion == "call" and c1 <= c2:
        return None

    if direccion == "put" and c1 > o1:
        return None
    if direccion == "call" and c1 < o1:
        return None

    # ⏱️ ENTRADA SIGUIENTE VELA
    segundos = int(time.time()) % 60
    esperar = 60 - segundos

    if esperar > 0:
        time.sleep(esperar)

    ultima_operacion = time.time()

    return par, direccion


# =========================
# OPERAR
# =========================
def operar(iq, par, direccion):
    print(f"🔥 {par} → {direccion}")

    check, _ = iq.buy(MONTO, par, direccion, 1)

    if check:
        print("✅ OPERACIÓN ABIERTA")

        enviar_mensaje(f"""
🚀 ENTRADA PRO

Par: {par}
Dirección: {direccion.upper()}
Monto: ${MONTO}
Expiración: 1 MIN
""")
    else:
        print("❌ Error al operar")


# =========================
# LOOP
# =========================
def run():
    iq = conectar()

    while True:
        try:

            if not iq.check_connect():
                iq = conectar()

            data = {}

            for par in PARES:
                data[par] = obtener_velas(iq, par)

            resultado = detectar_entrada(data)

            if resultado:
                par, direccion = resultado
                operar(iq, par, direccion)
                time.sleep(60)
            else:
                print("🔎 Buscando condiciones PERFECTAS...")

            time.sleep(2)

        except Exception as e:
            print("ERROR:", e)
            time.sleep(5)


# =========================
# START
# =========================
if __name__ == "__main__":
    run()
