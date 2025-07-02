import requests

def send_telegram(bot_token, chat_id, message):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    data = {"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}
    try:
        response = requests.post(url, data=data)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Telegram Error: {e}")

def get_price_action_patterns(df):
    patterns = []
    last = df.iloc[-2:]
    if last['Close'].iloc[-2] < last['Open'].iloc[-2] and last['Close'].iloc[-1] > last['Open'].iloc[-1]:
        patterns.append("Bullish Engulfing")
    if last['Close'].iloc[-2] > last['Open'].iloc[-2] and last['Close'].iloc[-1] < last['Open'].iloc[-1]:
        patterns.append("Bearish Engulfing")
    return patterns
