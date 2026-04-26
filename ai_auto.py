import json
import os
from datetime import datetime

STATS_FILE = "stats.json"
TRADES_FILE = "trades.json"

def load(file, default):
    if not os.path.exists(file):
        return default
    with open(file, "r") as f:
        return json.load(f)

def save(file, data):
    with open(file, "w") as f:
        json.dump(data, f)

def register_trade(pair, direction, result):

    stats = load(STATS_FILE, {"wins":0,"losses":0})
    trades = load(TRADES_FILE, [])

    if result == "win":
        stats["wins"] += 1
    else:
        stats["losses"] += 1

    trades.append({
        "pair": pair,
        "direction": direction,
        "result": result,
        "time": str(datetime.now())
    })

    save(STATS_FILE, stats)
    save(TRADES_FILE, trades)
