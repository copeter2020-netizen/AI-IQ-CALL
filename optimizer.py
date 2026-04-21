import pandas as pd
import itertools
import estrategia
from estrategia import calculate_indicators, check_buy_signal, check_sell_signal

EXPIRATION = 1

PARAM_GRID = {
    "MIN_BODY": [0.0002, 0.00025, 0.0003],
    "MIN_WIDTH": [0.0005, 0.0006, 0.0007],
    "TOL": [0.0002, 0.0003, 0.0004]
}

def run_backtest(df):
    wins, losses, trades = 0, 0, 0

    for i in range(50, len(df) - EXPIRATION - 1):
        sub_df = df.iloc[:i+1]

        buy = check_buy_signal(sub_df)
        sell = check_sell_signal(sub_df)

        entry = df.iloc[i+1]
        result = df.iloc[i+1 + EXPIRATION]

        if buy:
            trades += 1
            wins += result['close'] > entry['open']
            losses += result['close'] <= entry['open']

        elif sell:
            trades += 1
            wins += result['close'] < entry['open']
            losses += result['close'] >= entry['open']

    if trades < 30:
        return None

    winrate = wins / trades
    profit = (wins * 0.8) - losses

    return {"winrate": winrate, "profit": profit}

def optimize_pair(df, pair):

    df = calculate_indicators(df)

    best = None
    keys = PARAM_GRID.keys()

    for values in itertools.product(*PARAM_GRID.values()):
        config = dict(zip(keys, values))

        estrategia.MIN_BODY = config["MIN_BODY"]
        estrategia.MIN_WIDTH = config["MIN_WIDTH"]
        estrategia.TOL = config["TOL"]

        result = run_backtest(df)

        if not result:
            continue

        if not best or result["profit"] > best["profit"]:
            best = {**result, "config": config}

    print(pair, "=>", best)
