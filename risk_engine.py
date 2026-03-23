import random

def monte_carlo(winrate,risk,trades=1000):

    balance=1000

    for _ in range(trades):

        if random.random()<winrate:

            balance+=balance*risk

        else:

            balance-=balance*risk

    return balance
