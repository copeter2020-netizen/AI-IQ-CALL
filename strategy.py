import time
import json
import os

DB_FILE = "ia_data.json"


# ==========================
# 🧠 CARGAR DATOS IA
# ==========================
def cargar_datos():
    if not os.path.exists(DB_FILE):
        return {}

    try:
        with open(DB_FILE, "r") as f:
            return json.load(f)
    except:
        return {}


# ==========================
# 💾 GUARDAR DATOS IA
# ==========================
def guardar_datos(data):
    try:
        with open(DB_FILE, "w") as f:
            json.dump(data, f)
    except:
        pass


# ==========================
# 📊 REGISTRAR RESULTADO
# ==========================
def registrar_resultado(par, resultado):

    data = cargar_datos()

    if par not in data:
        data[par] = {"win": 0, "loss": 0}

    if resultado == "win":
        data[par]["win"] += 1
    else:
        data[par]["loss"] += 1

    guardar_datos(data)


# ==========================
# 🧠 FILTRO IA (WINRATE)
# ==========================
def par_permitido(par):

    data = cargar_datos()

    if par not in data:
        return True  # nuevo par → probar

    wins = data[par]["win"]
    loss = data[par]["loss"]

    total = wins + loss

    if total < 5:
        return True  # no hay suficiente info

    winrate = wins / total

    return winrate >= 0.6  # 🔥 SOLO BUENOS PARES


# ==========================
# 🔥 FILTRO PAYOUT
# ==========================
def payout_valido(iq, par, minimo=70):
    try:
        profit = iq.get_all_profit()
        p = profit.get(par, {})
        return p.get("digital", 0) >= minimo
    except:
        return False


# ==========================
# 🧠 ESTRATEGIA IA
# ==========================
def detectar_trampa(iq, par):

    # 🔥 IA FILTRO
    if not par_permitido(par):
        return None

    # 🔥 PAYOUT
    if not payout_valido(iq, par):
        return None

    try:
        velas = iq.get_candles(par, 60, 100, time.time())
    except:
        return None

    if not velas or len(velas) < 50:
        return None

    vela_base = velas[-5]
    vela_prev = velas[-4]
    vela_trampa = velas[-3]

    def cuerpo(v):
        return abs(v["close"] - v["open"])

    def rango(v):
        return v["max"] - v["min"]

    if rango(vela_trampa) == 0:
        return None

    score = 0

    # 🔥 CONTINUACIÓN
    if (
        vela_base["close"] > vela_base["open"] and
        vela_prev["close"] > vela_prev["open"]
    ) or (
        vela_base["close"] < vela_base["open"] and
        vela_prev["close"] < vela_prev["open"]
    ):
        score += 1
    else:
        return None

    # 🔥 TRAMPA (LIQUIDEZ)
    maximo = max(v["max"] for v in velas[-50:-3])
    minimo = min(v["min"] for v in velas[-50:-3])

    sweep_alcista = vela_trampa["max"] > maximo
    sweep_bajista = vela_trampa["min"] < minimo

    if sweep_alcista or sweep_bajista:
        score += 2
    else:
        return None

    # 🔥 RECHAZO
    mecha_sup = vela_trampa["max"] - max(vela_trampa["close"], vela_trampa["open"])
    mecha_inf = min(vela_trampa["close"], vela_trampa["open"]) - vela_trampa["min"]

    if mecha_sup > cuerpo(vela_trampa) or mecha_inf > cuerpo(vela_trampa):
        score += 1

    # 🔥 ESTRUCTURA
    estructura = velas[-15:-3]
    alc = sum(1 for v in estructura if v["close"] > v["open"])
    baj = sum(1 for v in estructura if v["close"] < v["open"])

    if alc >= 10 or baj >= 10:
        score += 1

    if score < 4:
        return None

    # 🔻 PUT
    if sweep_alcista and vela_trampa["close"] < vela_trampa["open"]:
        return {"action": "put"}

    # 🔺 CALL
    if sweep_bajista and vela_trampa["close"] > vela_trampa["open"]:
        return {"action": "call"}

    return None
