import json
import os

DATA_FILE = "trades.json"

# ================= LOAD =================

def load():
    if not os.path.exists(DATA_FILE):
        return {"wins": 0, "losses": 0}
    
    with open(DATA_FILE, "r") as f:
        return json.load(f)

# ================= SAVE =================

def save(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

# ================= PREDICT =================

def predict():
    data = load()

    total = data["wins"] + data["losses"]

    if total < 10:
        return True  # 🔥 operar siempre al inicio

    winrate = data["wins"] / total

    # 🔥 FILTRO INTELIGENTE
    if winrate >= 0.55:
        return True
    else:
        return False

# ================= SAVE TRADE =================

def save_trade(result):
    data = load()

    if result == "win":
        data["wins"] += 1
    else:
        data["losses"] += 1

    save(data)
