import os
import requests

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

URL = f"https://api.telegram.org/bot{TOKEN}/sendMessage" if TOKEN else None


def send_message(text):

    # 🔴 VALIDACIÓN
    if not TOKEN or not CHAT_ID:
        print("❌ TELEGRAM NO CONFIGURADO")
        return

    try:
        response = requests.post(
            URL,
            json={
                "chat_id": CHAT_ID,
                "text": str(text)
            },
            timeout=5
        )

        # 🔥 VALIDAR RESPUESTA REAL DE TELEGRAM
        if response.status_code != 200:
            print(f"❌ Error HTTP Telegram: {response.status_code}")
            return

        data = response.json()

        if not data.get("ok"):
            print(f"❌ Telegram respondió error: {data}")
            return

    except requests.exceptions.Timeout:
        print("⏳ Timeout Telegram")

    except requests.exceptions.ConnectionError:
        print("🌐 Error conexión Telegram")

    except Exception as e:
        print("❌ Error Telegram:", e)
