import os
import requests


def send_message(text):

    TOKEN = os.getenv("TELEGRAM_TOKEN")
    CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

    # 🔴 VALIDACIÓN FUERTE
    if not TOKEN or not CHAT_ID:
        print("❌ TELEGRAM NO CONFIGURADO")
        print("TOKEN:", TOKEN)
        print("CHAT_ID:", CHAT_ID)
        return

    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

    try:
        response = requests.post(
            url,
            json={
                "chat_id": CHAT_ID,
                "text": str(text)
            },
            timeout=10
        )

        # 🔥 DEBUG REAL (IMPORTANTE)
        print("📡 Telegram status:", response.status_code)
        print("📡 Telegram respuesta:", response.text)

        if response.status_code != 200:
            print("❌ Error HTTP Telegram")
            return

        data = response.json()

        if not data.get("ok"):
            print("❌ Error Telegram:", data)
            return

    except requests.exceptions.Timeout:
        print("⏳ Timeout Telegram")

    except requests.exceptions.ConnectionError:
        print("🌐 Error conexión Telegram")

    except Exception as e:
        print("❌ Error Telegram:", e)
