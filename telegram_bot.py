import os
import requests

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

URL = f"https://api.telegram.org/bot{TOKEN}"


def send_message(text):
    try:
        requests.post(
            f"{URL}/sendMessage",
            data={
                "chat_id": CHAT_ID,
                "text": text
            },
            timeout=5
        )
    except:
        pass


def send_image(url, caption=""):
    try:
        requests.post(
            f"{URL}/sendPhoto",
            data={
                "chat_id": CHAT_ID,
                "caption": caption,
                "photo": url
            },
            timeout=10
        )
    except:
        pass
