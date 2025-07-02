import json
import time
import requests
import pytz
import traceback
import yfinance as yf
import pandas as pd
import ta
from datetime import datetime
from utils import get_price_action_patterns, send_telegram
from okx.trade import Trade  # ✅ تم التعديل هنا

# تحميل الإعدادات
with open("config.json", "r") as f:
    config = json.load(f)

# إعدادات المنطقة الزمنية
timezone = pytz.timezone("Asia/Baghdad")
symbols = config["symbols"]
intervals = config["intervals"]

# إعداد واجهة OKX التجريبية
okx_trade = Trade(
    api_key=config["okx"]["api_key"],
    api_secret_key=config["okx"]["api_secret"],
    passphrase=config["okx"]["passphrase"],
    flag="1"  # 1 يعني Demo
)

# إرسال تنبيه عند بدء التشغيل
send_telegram("✅ البوت بدأ العمل وسيتم التحديث كل 5 دقائق حقيقية.")

def fetch_data(symbol, interval):
    df = yf.download(symbol, period="7d", interval=interval, auto_adjust=True)
    if df.empty or len(df) < 30:
        return None

    df['rsi'] = ta.momentum.RSIIndicator(df['Close'], window=14).rsi()
    macd = ta.trend.MACD(df['Close'])
    df['macd'] = macd.macd()
    df['macd_signal'] = macd.macd_signal()
    stoch = ta.momentum.StochasticOscillator(df['High'], df['Low'], df['Close'])
    df['stoch_k'] = stoch.stoch()
    df['stoch_d'] = stoch.stoch_signal()

    df.dropna(inplace=True)
    return df

def analyze(symbol):
    signals = []
    for interval in intervals:
        df = fetch_data(symbol, interval)
        if df is None:
            continue
        pattern = get_price_action_patterns(df)
        signals.append(f"{interval}: {pattern}")

    now = datetime.now(timezone).strftime("%Y-%m-%d %H:%M:%S")
    message = f"📊 *{symbol} إشارات البرايس أكشن:*\n\n" + "\n".join(signals) + f"\n\n⏰ *الوقت:* {now}"
    send_telegram(message)

def run_bot():
    last_minute = -1
    while True:
        now = datetime.now(timezone)
        if now.minute % 5 == 0 and now.minute != last_minute:
            last_minute = now.minute
            try:
                for symbol in symbols:
                    analyze(symbol)
            except Exception:
                error = traceback.format_exc()
                send_telegram(f"❌ توقف البوت بسبب خطأ:\n```{error}```")
        time.sleep(5)

if __name__ == "__main__":
    run_bot()
