import json
import os
from datetime import datetime

STATS_FILE = "stats.json"
TRADES_FILE = "trades.json"

# ===============================
# CARGAR / GUARDAR
# ===============================

def load(file, default):
    try:
        if not os.path.exists(file):
            return default
        with open(file, "r") as f:
            return json.load(f)
    except:
        return default


def save(file, data):
    try:
        with open(file, "w") as f:
            json.dump(data, f)
    except:
        pass


# ===============================
# 🧠 IA FILTRO
# ===============================

def allow_trade(score):

    stats = load(STATS_FILE, {"wins": 0, "losses": 0})
    total = stats["wins"] + stats["losses"]

    # 🔹 Sin datos → permitir
    if total < 20:
        return score >= 3

    winrate = stats["wins"] / total

    # 🔴 Va mal → más estricto
    if winrate < 0.55:
        return score >= 4

    # 🟢 Va bien → normal
    if winrate > 0.65:
        return score >= 3

    # 🟡 Medio → estricto
    return score >= 4


# ===============================
# 📊 REGISTRAR TRADE
# ===============================

def register_trade(pair, direction, result):

    stats = load(STATS_FILE, {"wins": 0, "losses": 0})
    trades = load(TRADES_FILE, [])

    # actualizar stats
    if result == "win":
        stats["wins"] += 1
    else:
        stats["losses"] += 1

    # guardar trade
    trades.append({
        "pair": pair,
        "direction": direction,
        "result": result,
        "time": datetime.utcnow().isoformat()
    })

    save(STATS_FILE, stats)
    save(TRADES_FILE, trades)
