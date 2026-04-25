import requests
import os

def send_telegram(msg: str):
    token = os.getenv("TG_TOKEN")
    chat_id = os.getenv("TG_CHAT_ID")

    if not token or not chat_id:
        print("⚠️ Telegram未配置")
        return

    url = f"https://api.telegram.org/bot{token}/sendMessage"

    payload = {
        "chat_id": chat_id,
        "text": msg,
        "parse_mode": "Markdown"
    }

    requests.post(url, json=payload)