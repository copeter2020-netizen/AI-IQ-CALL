import requests

TELEGRAM_TOKEN = "TU_TOKEN"
CHAT_ID = "TU_CHAT_ID"

def enviar_mensaje(texto):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, data={
            "chat_id": CHAT_ID,
            "text": texto
        }, timeout=5)
    except Exception as e:
        print("⚠️ Error Telegram:", e)
