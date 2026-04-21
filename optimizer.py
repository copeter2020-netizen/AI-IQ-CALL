import pandas as pd
import itertools
import estrategia
from estrategia import calculate_indicators, check_buy_signal, check_sell_signal

# ================= CONFIG =================

PAIR = "EURUSD-OTC"
EXPIRATION = 1
MIN_TRADES = 30

PARAM_GRID = {
    "MIN_BODY": [0.0002, 0.00025, 0.0003, 0.00035],
    "MIN_WIDTH": [0.0005, 0.0006, 0.0007, 0.0008],
    "TOL": [0.0002, 0.0003, 0.0004]
}

# ================= BACKTEST =================

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
            if result['close'] > entry['open']:
                wins += 1
            else:
                losses += 1

        elif sell:
            trades += 1
            if result['close'] < entry['open']:
                wins += 1
            else:
                losses += 1

    if trades < MIN_TRADES:
        return None

    winrate = wins / trades
    profit = (wins * 0.8) - losses
    score = profit * winrate

    return {
        "trades": trades,
        "winrate": winrate,
        "profit": profit,
        "score": score
    }

# ================= SPLIT =================

def split_data(df, ratio=0.7):
    split = int(len(df) * ratio)
    return df[:split], df[split:]

# ================= OPTIMIZACIÓN =================

def optimize(df):

    print(f"\n🔎 OPTIMIZANDO {PAIR}\n")

    # si viene con múltiples pares
    if "pair" in df.columns:
        df = df[df["pair"] == PAIR].reset_index(drop=True)

    df = calculate_indicators(df)

    train_df, test_df = split_data(df)

    keys = PARAM_GRID.keys()
    combinations = list(itertools.product(*PARAM_GRID.values()))

    best = None

    print(f"Probando {len(combinations)} configuraciones...\n")

    for values in combinations:

        config = dict(zip(keys, values))

        estrategia.MIN_BODY = config["MIN_BODY"]
        estrategia.MIN_WIDTH = config["MIN_WIDTH"]
        estrategia.TOL = config["TOL"]

        train = run_backtest(train_df)
        if not train:
            continue

        test = run_backtest(test_df)
        if not test:
            continue

        stability = abs(train["winrate"] - test["winrate"])
        final_score = test["score"] - stability

        print(
            f"{config} | "
            f"Train WR: {train['winrate']:.2f} | "
            f"Test WR: {test['winrate']:.2f} | "
            f"Score: {final_score:.2f}"
        )

        if not best or final_score > best["score"]:
            best = {
                "config": config,
                "train": train,
                "test": test,
                "stability": stability,
                "score": final_score
            }

    print("\n🏆 MEJOR CONFIGURACIÓN:\n")
    print(best)

    return best
