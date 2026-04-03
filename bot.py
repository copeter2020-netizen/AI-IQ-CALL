import time
import os
import requests
import numpy as np
from iqoptionapi.stable_api import IQ_Option

EMAIL = os.getenv("IQ_EMAIL")
PASSWORD = os.getenv("IQ_PASSWORD")

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

MONTO = 13
CUENTA = "PRACTICE"

PARES = [
    "EURUSD-OTC",
    "GBPUSD-OTC",
    "EURJPY-OTC",
    "EURGBP-OTC",
    "USDCHF-OTC"
]

ultima_operacion = 0


def enviar_mensaje(texto):
    try:
        if TOKEN and CHAT_ID:
            requests.post(
                f"https://api.telegram.org/bot{TOKEN}/sendMessage",
                data={"chat_id": CHAT_ID, "text": texto},
                timeout=5
            )
    except:
        pass


def conectar():
    while True:
        try:
            iq = IQ_Option(EMAIL, PASSWORD)
            iq.connect()

            if iq.check_connect():
                print("✅ CONECTADO")
                iq.change_balance(CUENTA)
                return iq
            else:
                print("❌ Error credenciales")
                time.sleep(5)
        except:
            time.sleep(5)


def obtener_velas(iq, par):
    try:
        velas = iq.get_candles(par, 60, 120, time.time())
        return [{
            "open": v["open"],
            "close": v["close"],
            "max": v["max"],
            "min": v["min"]
        } for v in velas]
    except:
        return []


# =========================
# 🔥 ESTRATEGIA ULTRA PRO
# =========================
def detectar_mejor_entrada(data_por_par):
    global ultima_operacion

    ahora = time.time()

    # 🔒 ULTRA SELECTIVO
    if ahora - ultima_operacion < 1800:  # 30 min mínimo
        return None

    # ⏱️ SOLO AL FINAL
    if int(ahora) % 60 < 58:
        return None

    mejor = None
    mejor_score = 0

    for par, velas in data_por_par.items():

        if len(velas) < 120:
            continue

        closes = np.array([float(v["close"]) for v in velas])
        highs  = np.array([float(v["max"]) for v in velas])
        lows   = np.array([float(v["min"]) for v in velas])

        # 🔥 BLOQUE 5 VELAS PERFECTAS
        bloque = velas[-6:-1]

        alcistas = sum(1 for v in bloque if v["close"] > v["open"])
        bajistas = sum(1 for v in bloque if v["close"] < v["open"])

        if alcistas == 5:
            direccion = "call"
        elif bajistas == 5:
            direccion = "put"
        else:
            continue

        score = 30

        # 🔥 VELA ACTUAL
        v1 = velas[-1]
        v2 = velas[-2]
        v3 = velas[-3]

        o1,c1,h1,l1 = float(v1["open"]), float(v1["close"]), float(v1["max"]), float(v1["min"])
        o2,c2 = float(v2["open"]), float(v2["close"])
        c3 = float(v3["close"])

        rango = h1 - l1
        if rango == 0:
            continue

        cuerpo = abs(c1 - o1)

        mecha_sup = h1 - max(o1, c1)
        mecha_inf = min(o1, c1) - l1

        posicion = (c1 - l1) / rango

        # 🔥 CIERRE EXTREMO
        if direccion == "call":
            if posicion < 0.9 or mecha_sup > cuerpo * 0.25:
                continue
        else:
            if posicion > 0.1 or mecha_inf > cuerpo * 0.25:
                continue

        score += 25

        # 🔥 CONTINUIDAD PERFECTA
        if direccion == "call" and not (c1 > c2 > c3):
            continue
        if direccion == "put" and not (c1 < c2 < c3):
            continue

        score += 20

        # 🔥 CUERPO DOMINANTE
        if cuerpo < rango * 0.75:
            continue

        score += 10

        # 🔥 MOMENTUM CORTO (REAL)
        p = np.polyfit(range(5), closes[-5:], 1)[0]

        if direccion == "call" and p <= 0:
            continue
        if direccion == "put" and p >= 0:
            continue

        score += 15

        # 🔥 VOLATILIDAD REAL
        vol_now = np.mean(highs[-5:] - lows[-5:])
        vol_old = np.mean(highs[-20:] - lows[-20:])

        if vol_now <= vol_old:
            continue

        score += 10

        # 🔥 RUPTURA LIMPIA
        if direccion == "call" and c1 <= float(v2["max"]):
            continue
        if direccion == "put" and c1 >= float(v2["min"]):
            continue

        score += 10

        # 🔥 SELECCIÓN
        if score > mejor_score:
            mejor_score = score
            mejor = (par, direccion, score)

    # 🔥 SOLO PERFECTO
    if mejor and mejor_score >= 100:
        ultima_operacion = ahora
        return mejor

    return None


def operar(iq, par, direccion):
    print(f"🔥 {par} → {direccion}")

    check, _ = iq.buy(MONTO, par, direccion, 1)

    if check:
        print("✅ OPERACIÓN ABIERTA")
        enviar_mensaje(f"{par} → {direccion.upper()} 🚀")
    else:
        print("❌ ERROR")


def run():

    iq = conectar()

    while True:
        try:

            if not iq.check_connect():
                iq = conectar()

            data = {par: obtener_velas(iq, par) for par in PARES}

            resultado = detectar_mejor_entrada(data)

            if resultado:
                par, direccion, score = resultado

                print(f"✅ SETUP PERFECTO ({score})")

                segundos = int(time.time()) % 60
                esperar = 60 - segundos

                if esperar > 0:
                    time.sleep(esperar)

                operar(iq, par, direccion)

                time.sleep(60)

            else:
                print("🔎 MODO ULTRA SELECTIVO...")

            time.sleep(2)

        except Exception as e:
            print("ERROR:", e)
            time.sleep(5)


if __name__ == "__main__":
    run()
