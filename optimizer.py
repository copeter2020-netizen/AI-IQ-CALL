import pandas as pd
import itertools
import estrategia
from estrategia import calculate_indicators, check_buy_signal, check_sell_signal

# ================= CONFIG =================

EXPIRATION = 1

PARAM_GRID = {
    "MIN_BODY": [0.0002, 0.00025, 0.0003],
    "MIN_WIDTH": [0.0005, 0.0006, 0.0007],
    "TOL": [0.0002, 0.0003, 0.0004]
}

MIN_TRADES = 30  # evitar configs irrelevantes

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

    # 🎯 score más inteligente
    score = profit * winrate

    return {
        "trades": trades,
        "winrate": winrate,
        "profit": profit,
        "score": score
    }

# ================= SPLIT DATOS =================

def split_data(df, ratio=0.7):
    split = int(len(df) * ratio)
    return df[:split], df[split:]

# ================= OPTIMIZACIÓN =================

def optimize(df):

    df = calculate_indicators(df)

    train_df, test_df = split_data(df)

    keys = PARAM_GRID.keys()
    combinations = list(itertools.product(*PARAM_GRID.values()))

    results = []

    print(f"🔍 Probando {len(combinations)} configuraciones...\n")

    for values in combinations:

        config = dict(zip(keys, values))

        # aplicar config
        estrategia.MIN_BODY = config["MIN_BODY"]
        estrategia.MIN_WIDTH = config["MIN_WIDTH"]
        estrategia.TOL = config["TOL"]

        train_result = run_backtest(train_df)

        if not train_result:
            continue

        test_result = run_backtest(test_df)

        if not test_result:
            continue

        # 🎯 evitar sobreajuste
        stability = abs(train_result["winrate"] - test_result["winrate"])

        final_score = (
            test_result["score"] -
            stability  # penaliza inestabilidad
        )

        results.append({
            "config": config,
            "train": train_result,
            "test": test_result,
            "stability": stability,
            "final_score": final_score
        })

        print(
            f"{config} | "
            f"Train WR: {train_result['winrate']:.2f} | "
            f"Test WR: {test_result['winrate']:.2f} | "
            f"Score: {final_score:.2f}"
        )

    # ================= TOP RESULTADOS =================

    results = sorted(results, key=lambda x: x["final_score"], reverse=True)

    print("\n🏆 TOP 5 CONFIGURACIONES:\n")

    for r in results[:5]:
        print("Config:", r["config"])
        print("Train:", r["train"])
        print("Test:", r["test"])
        print("Stability:", r["stability"])
        print("Score:", r["final_score"])
        print("-" * 40)
