import requests
import os

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


def enviar_panel():
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

    teclado = {
        "keyboard": [
            ["EURUSD", "GBPUSD", "EURJPY"],
            ["USDCHF", "GBPJPY", "USDZAR"],
            ["1M", "2M", "3M", "5M"],
            ["▶️ START", "⏹ STOP"]
        ],
        "resize_keyboard": True
    }

    requests.post(url, json={
        "chat_id": CHAT_ID,
        "text": "📊 PANEL DE CONTROL",
        "reply_markup": teclado
    })


if __name__ == "__main__":
    enviar_panel()
