import json
import os

FILE = "stats.json"

def load():
    if not os.path.exists(FILE):
        return {"wins": 0, "losses": 0}
    with open(FILE, "r") as f:
        return json.load(f)

def allow_trade(score):
    data = load()
    total = data["wins"] + data["losses"]

    if total < 20:
        return score >= 3

    winrate = data["wins"] / total

    if winrate < 0.55:
        return score >= 4

    if winrate > 0.65:
        return score >= 3

    return score >= 4
