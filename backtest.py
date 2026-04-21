import pandas as pd
from estrategia import calculate_indicators, check_buy_signal, check_sell_signal

EXPIRATION = 1

def run_backtest(df):
    df = calculate_indicators(df)

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
        print("No trades")
        return

    winrate = (wins / trades) * 100
    profit = (wins * 0.8) - losses

    print("\nRESULTADOS")
    print("Trades:", trades)
    print("Winrate:", winrate)
    print("Profit:", profit)
