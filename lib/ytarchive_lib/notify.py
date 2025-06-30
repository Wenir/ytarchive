import requests


def send_message(message, config, with_notification=True, strict=True):
    url = f"https://api.telegram.org/bot{config["TG_BOT_TOKEN"]}/sendMessage"

    # Request payload
    payload = {
        "chat_id": config["TG_CHAT_ID"],
        "text": message,
        "disable_notification": not with_notification,
        #"parse_mode": "Markdown"  # Optional: Use "HTML" or "Markdown" for formatting
    }

    response = requests.post(url, json=payload)
    if strict:
        response.raise_for_status()