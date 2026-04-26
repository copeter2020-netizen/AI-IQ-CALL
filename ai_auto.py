import json
import os

FILE = "data.json"

def load():
    if not os.path.exists(FILE):
        return {"wins": 0, "losses": 0}
    with open(FILE, "r") as f:
        return json.load(f)

def save(data):
    with open(FILE, "w") as f:
        json.dump(data, f)

def predict():
    data = load()
    total = data["wins"] + data["losses"]

    if total < 10:
        return True

    winrate = data["wins"] / total
    return winrate >= 0.55

def save_trade(result):
    data = load()

    if result == "win":
        data["wins"] += 1
    else:
        data["losses"] += 1

    save(data)
