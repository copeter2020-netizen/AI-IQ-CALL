import json
import os

FILE = "stats.json"

def load():
    if not os.path.exists(FILE):
        return {"wins": 0, "losses": 0}
    with open(FILE, "r") as f:
        return json.load(f)

def save(data):
    with open(FILE, "w") as f:
        json.dump(data, f)

# 🔥 usa balance REAL
def get_amount(balance):
    return round(balance * 0.03, 2)  # 3% por trade

def register_trade(result):
    data = load()

    if result == "win":
        data["wins"] += 1
    else:
        data["losses"] += 1

    save(data)

def allow_trade(score):
    return score >= 2
