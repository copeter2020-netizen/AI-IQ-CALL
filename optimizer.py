import pandas as pd
import itertools
from estrategia import calculate_indicators, check_buy_signal, check_sell_signal

# ================= CONFIG =================

EXPIRATION = 1

# 🔥 RANGOS A PROBAR (puedes ampliarlos)
PARAM_GRID = {
    "MIN_BODY": [0.0002, 0.00025, 0.0003],
    "MIN_WIDTH": [0.0005, 0.0006, 0.0007],
    "TOL": [0.0002, 0.0003, 0.0004]
}

# ================= BACKTEST =================

def run_backtest(df):
    wins = 0
    losses = 0
    trades = 0

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

    if trades == 0:
        return None

    winrate = wins / trades
    profit = (wins * 0.8) - losses

    return {
        "trades": trades,
        "winrate": winrate,
        "profit": profit
    }

# ================= OPTIMIZADOR =================

def optimize(df):

    df = calculate_indicators(df)

    keys = PARAM_GRID.keys()
    combinations = list(itertools.product(*PARAM_GRID.values()))

    best_result = None
    best_config = None

    print(f"🔍 Probando {len(combinations)} combinaciones...\n")

    for values in combinations:

        # aplicar parámetros dinámicamente
        config = dict(zip(keys, values))

        # 🔥 inyectar valores en estrategia
        import estrategia
        estrategia.MIN_BODY = config["MIN_BODY"]
        estrategia.MIN_WIDTH = config["MIN_WIDTH"]
        estrategia.TOL = config["TOL"]

        result = run_backtest(df)

        if result is None:
            continue

        print(
            f"Config: {config} | "
            f"WR: {result['winrate']:.2f} | "
            f"Trades: {result['trades']} | "
            f"Profit: {result['profit']:.2f}"
        )

        # criterio: maximizar profit
        if best_result is None or result["profit"] > best_result["profit"]:
            best_result = result
            best_config = config

    # ================= RESULTADO FINAL =================

    print("\n🏆 MEJOR CONFIGURACIÓN:")
    print(best_config)
    print("Resultado:", best_result)
