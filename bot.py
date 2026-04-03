import time
import os
import requests
import numpy as np
from iqoptionapi.stable_api import IQ_Option

# =========================
# VARIABLES RAILWAY
# =========================
EMAIL = os.getenv("IQ_EMAIL")
PASSWORD = os.getenv("IQ_PASSWORD")

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

MONTO = 12
CUENTA = "PRACTICE"

PARES = [
    "EURUSD-OTC",
    "GBPUSD-OTC",
    "EURJPY-OTC",
    "EURGBP-OTC",
    "USDCHF-OTC"
]

ultima_operacion = 0


# =========================
# 🔥 TELEGRAM (FIX + DEBUG)
# =========================
def enviar_mensaje(texto):
    try:
        if not TOKEN or not CHAT_ID:
            print("⚠️ Telegram no configurado")
            return

        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

        response = requests.post(url, data={
            "chat_id": CHAT_ID,
            "text": texto
        }, timeout=5)

        print("📩 Telegram status:", response.status_code)
        print("📩 Telegram response:", response.text)

    except Exception as e:
        print("❌ Error Telegram:", e)


# =========================
# CONEXIÓN
# =========================
def conectar():
    while True:
        try:
            if not EMAIL or not PASSWORD:
                print("❌ Faltan credenciales en Railway")
                time.sleep(10)
                continue

            iq = IQ_Option(EMAIL, PASSWORD)
            iq.connect()

            if iq.check_connect():
                print("✅ CONECTADO A IQ OPTION")
                iq.change_balance(CUENTA)
                return iq
            else:
                print("❌ Credenciales incorrectas")
                time.sleep(10)

        except Exception as e:
            print("Error conexión:", e)
            time.sleep(10)


# =========================
# VELAS
# =========================
def obtener_velas(iq, par):
    try:
        velas = iq.get_candles(par, 60, 120, time.time())

        return [{
            "open": v.get("open", 0),
            "close": v.get("close", 0),
            "max": v.get("max", 0),
            "min": v.get("min", 0)
        } for v in velas]

    except Exception as e:
        print("Error velas:", e)
        return []


# =========================
# 🔥 FILTRO MERCADO ACTIVO
# =========================
def mercado_activo(velas):
    try:
        highs = np.array([float(v["max"]) for v in velas])
        lows  = np.array([float(v["min"]) for v in velas])

        vol_actual = np.mean(highs[-5:] - lows[-5:])
        vol_pasada = np.mean(highs[-30:] - lows[-30:])

        rango = max(highs[-20:]) - min(lows[-20:])

        if vol_actual < vol_pasada * 0.8:
            return False

        if rango < vol_actual * 2:
            return False

        return True

    except:
        return False


# =========================
# ESTRATEGIA
# =========================
def detectar_mejor_entrada(data_por_par):
    global ultima_operacion

    ahora = time.time()

    if ahora - ultima_operacion < 10800:
        return None

    if int(ahora) % 60 < 58:
        return None

    mejor = None
    mejor_score = 0

    for par, velas in data_por_par.items():

        if len(velas) < 120:
            continue

        if not mercado_activo(velas):
            continue

        closes = np.array([float(v["close"]) for v in velas])
        highs  = np.array([float(v["max"]) for v in velas])
        lows   = np.array([float(v["min"]) for v in velas])

        v1 = velas[-1]
        v2 = velas[-2]
        v3 = velas[-3]

        o1,c1,h1,l1 = float(v1["open"]), float(v1["close"]), float(v1["max"]), float(v1["min"])
        o2,c2,h2,l2 = float(v2["open"]), float(v2["close"]), float(v2["max"]), float(v2["min"])
        o3,c3,_,_   = float(v3["open"]), float(v3["close"]), float(v3["max"]), float(v3["min"])

        rango = h1 - l1
        if rango == 0:
            continue

        cuerpo = abs(c1 - o1)
        mecha_sup = h1 - max(o1, c1)
        mecha_inf = min(o1, c1) - l1

        posicion = (c1 - l1) / rango

        score = 0

        hh = highs[-1] > highs[-5] > highs[-10]
        hl = lows[-1] > lows[-5] > lows[-10]

        ll = highs[-1] < highs[-5] < highs[-10]
        lh = lows[-1] < lows[-5] < lows[-10]

        if hh and hl:
            direccion = "call"
            score += 20
        elif ll and lh:
            direccion = "put"
            score += 20
        else:
            continue

        if direccion == "call" and not (c1 > c2 > c3):
            continue
        if direccion == "put" and not (c1 < c2 < c3):
            continue

        score += 15

        if direccion == "call":
            if posicion < 0.85 or mecha_sup > cuerpo * 0.3:
                continue
        else:
            if posicion > 0.15 or mecha_inf > cuerpo * 0.3:
                continue

        score += 25

        if cuerpo < rango * 0.7:
            continue

        score += 10

        p1 = np.polyfit(range(20), closes[-20:], 1)[0]
        p2 = np.polyfit(range(5), closes[-5:], 1)[0]

        if direccion == "call" and not (p2 > p1 > 0):
            continue
        if direccion == "put" and not (p2 < p1 < 0):
            continue

        score += 10

        if direccion == "call" and c1 <= h2:
            continue
        if direccion == "put" and c1 >= l2:
            continue

        score += 10

        vol_now = np.mean(highs[-10:] - lows[-10:])
        vol_old = np.mean(highs[-40:] - lows[-40:])

        if vol_now <= vol_old:
            continue

        score += 10

        if score > mejor_score:
            mejor_score = score
            mejor = (par, direccion, score)

    if mejor and mejor_score >= 95:
        ultima_operacion = ahora
        return mejor

    return None


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
Expiración: 1 MIN
Monto: ${MONTO}
""")
    else:
        print("❌ No ejecutada")


# =========================
# LOOP
# =========================
def run():

    iq = conectar()

    # 🔥 MENSAJE DE PRUEBA
    enviar_mensaje("✅ BOT INICIADO CORRECTAMENTE")

    while True:
        try:

            if not iq.check_connect():
                print("🔄 Reconectando...")
                iq = conectar()

            data = {par: obtener_velas(iq, par) for par in PARES}

            resultado = detectar_mejor_entrada(data)

            if resultado:
                par, direccion, score = resultado

                print(f"✅ CONDICIÓN PERFECTA ({score})")

                segundos = int(time.time()) % 60
                esperar = 60 - segundos

                if esperar > 0:
                    time.sleep(esperar)

                operar(iq, par, direccion)

                time.sleep(60)

            else:
                print("🔎 Buscando condiciones PERFECTAS...")

            time.sleep(2)

        except Exception as e:
            print("ERROR LOOP:", e)
            time.sleep(5)


# =========================
# START
# =========================
if __name__ == "__main__":
    run() 
