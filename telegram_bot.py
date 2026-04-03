import requests

TOKEN = "AQUI_TU_TOKEN"
CHAT_ID = "AQUI_TU_CHAT_ID"

def enviar_mensaje(texto):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        data = {
            "chat_id": CHAT_ID,
            "text": texto
        }
        requests.post(url, data=data, timeout=5)
    except Exception as e:
        print("Error Telegram:", e)
