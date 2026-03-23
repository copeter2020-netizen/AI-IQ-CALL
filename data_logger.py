import os
from datetime import datetime

FILE_NAME = "trades_log.csv"

def init_file():
    if not os.path.exists(FILE_NAME):
        with open(FILE_NAME, "w") as f:
            f.write("fecha,par,accion,probabilidad,resultado\n")

def log_trade(pair, action, prob, win):
    try:
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        resultado = "WIN" if win else "LOSS"

        with open(FILE_NAME, "a") as f:
            f.write(f"{fecha},{pair},{action},{prob:.2f},{resultado}\n")

        print(f"📊 LOG: {pair} {action} {resultado}")

    except Exception as e:
        print("❌ Error guardando log:", e)
