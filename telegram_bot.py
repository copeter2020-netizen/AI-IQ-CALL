import os
import requests

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


def send_message(text):

    if not TOKEN or not CHAT_ID:
        print("❌ TELEGRAM NO CONFIGURADO")
        return

    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

        requests.post(
            url,
            data={
                "chat_id": CHAT_ID,
                "text": text
            },
            timeout=5
        )

    except Exception as e:
        print("❌ Error Telegram:", e)
