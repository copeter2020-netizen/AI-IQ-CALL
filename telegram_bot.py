import requests
import os

TOKEN = os.getenv("TELEGRAM_TOKEN")

# 🔥 REEMPLAZA ESTE ID POR EL DE TU GRUPO
CHAT_ID = "-1001234567890"


def send_message(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = {
        "chat_id": CHAT_ID,
        "text": text
    }
    requests.post(url, data=data)


def send_image(image_url, caption=""):
    url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
    data = {
        "chat_id": CHAT_ID,
        "photo": image_url,
        "caption": caption
    }
    requests.post(url, data=data)
