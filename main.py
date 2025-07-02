import yfinance as yf
import pandas as pd
import ta
import numpy as np
import requests
import time
import json
import pytz
from datetime import datetime
from scipy.signal import argrelextrema
import traceback
from utils import get_price_action_patterns, send_telegram
from okx import Trade as OkxTrade
from config import OKX_CONFIG, TELEGRAM_BOTS, SYMBOLS, TIMEZONE

# إرسال تنبيه بدء التشغيل
send_telegram("✅ البوت بدأ العمل بنجاح وسيحدث كل 5 دقائق (وقت حقيقي)")

def safe_float(val):
    try: return float(val)
    except: return float(val.item())

def find_support_levels(df, order=5):
    idx = argrelextrema(df['Close'].values, np.less_equal, order=order)[0]
    return df['Close'].iloc[idx].values

def find_resistance_levels(df, order=5):
    idx = argrelextrema(df['Close'].values, np.greater_equal, order=order)[0]
    return df['Close'].iloc[idx].values

def is_near_level(price, levels, threshold=0.005):
    return any(abs(price - level) / level < threshold for level in levels)

def format_message(symbol, close_val, signal, tp, sl, votes_buy, votes_sell,
                   rsi, macd_val, macd_sig, stoch_k, stoch_d,
                   bb_upper, bb_lower, adx_val, psar_val, pattern_summary, current_time):
    
    emoji = "🟢 BUY" if signal == "شراء" else ("🔴 SELL" if signal == "بيع" else "🟡 HOLD")
    return (
        f"📈 *{symbol}*\n"
        f"💰 *السعر:* `{close_val:.2f}`\n\n"
        f"⚡ *الإشارة:* {emoji}\n"
        f"🎯 *TP:* `{tp:.2f}` | ⛔ *SL:* `{sl:.2f}`\n\n"
        f"📊 *المؤشرات:*\n"
        f"  - RSI: `{rsi:.2f}`\n"
        f"  - MACD: `{macd_val:.2f}` / `{macd_sig:.2f}`\n"
        f"  - Stoch %K: `{stoch_k:.2f}` / %D: `{stoch_d:.2f}`\n"
        f"  - Bollinger Bands: ↑ `{bb_upper:.2f}` ↓ `{bb_lower:.2f}`\n"
        f"  - ADX: `{adx_val:.2f}`\n"
        f"  - PSAR: `{psar_val:.2f}`\n\n"
        f"🧮 *Votes:* 🟢 `{votes_buy}` | 🔴 `{votes_sell}`\n"
        f"📉 *برايس أكشن:*\n{pattern_summary}\n"
        f"⏰ {current_time}"
    )

def get_indicators(symbol, interval):
    df = yf.download(symbol, period='7d', interval=interval, auto_adjust=True)
    if df.empty:
        print(f"❌ لا توجد بيانات {symbol} للفريم {interval}")
        return None
    close = df['Close']
    high = df['High']
    low = df['Low']
    
    df['rsi'] = ta.momentum.RSIIndicator(close, window=14).rsi()
    macd = ta.trend.MACD(close)
    df['macd'] = macd.macd()
    df['macd_signal'] = macd.macd_signal()
    stoch = ta.momentum.StochasticOscillator(high, low, close)
    df['stoch_k'] = stoch.stoch()
    df['stoch_d'] = stoch.stoch_signal()
    bb = ta.volatility.BollingerBands(close)
    df['bb_upper'] = bb.bollinger_hband()
    df['bb_lower'] = bb.bollinger_lband()
    adx = ta.trend.ADXIndicator(high, low, close)
    df['adx'] = adx.adx()
    psar = ta.trend.PSARIndicator(high, low, close)
    df['psar'] = psar.psar()
    
    df.dropna(inplace=True)
    return df

def calculate_votes(df):
    close = safe_float(df['Close'].iloc[-1])
    rsi = safe_float(df['rsi'].iloc[-1])
    macd_v = safe_float(df['macd'].iloc[-1])
    macd_s = safe_float(df['macd_signal'].iloc[-1])
    st_k = safe_float(df['stoch_k'].iloc[-1])
    st_d = safe_float(df['stoch_d'].iloc[-1])
    bb_u = safe_float(df['bb_upper'].iloc[-1])
    bb_l = safe_float(df['bb_lower'].iloc[-1])
    adx = safe_float(df['adx'].iloc[-1])
    psar = safe_float(df['psar'].iloc[-1])
    
    supports = find_support_levels(df)
    resistances = find_resistance_levels(df)
    
    buy = sell = 0
    if rsi < 30: buy += 1
    elif rsi > 70: sell += 1
    if macd_v > macd_s: buy += 1
    elif macd_v < macd_s: sell += 1
    if st_k < 20 and st_k > st_d: buy += 1
    elif st_k > 80 and st_k < st_d: sell += 1
    if close < bb_l: buy += 1
    elif close > bb_u: sell += 1
    if adx >= 20: buy += 1
    if close > psar: buy += 1
    elif close < psar: sell += 1
    if is_near_level(close, supports): buy += 1
    if is_near_level(close, resistances): sell += 1
    
    return buy, sell, close, rsi, macd_v, macd_s, st_k, st_d, bb_u, bb_l, adx, psar

def analyze_symbol(symbol):
    timeframes = ['5m', '15m', '30m']
    total_buy = total_sell = 0
    last_vals = {}
    pattern_summary = []

    for tf in timeframes:
        df = get_indicators(symbol, tf)
        if df is None: continue
        buy, sell, *vals = calculate_votes(df)
        total_buy += buy
        total_sell += sell
        pattern = get_price_action_patterns(df)
        pattern_summary.append(f"{tf}: {pattern}")
        if tf == '30m':
            last_vals = dict(zip(
                ['close', 'rsi', 'macd', 'macd_s', 'st_k', 'st_d',
                 'bb_u', 'bb_l', 'adx', 'psar'], vals
            ))

    if not last_vals:
        return

    signal = "شراء" if total_buy > total_sell else "بيع" if total_sell > total_buy else "تريّث"
    close = last_vals['close']
    tp = close * (1.015 if signal == "شراء" else 0.985 if signal == "بيع" else 1)
    sl = close * (0.99 if signal == "شراء" else 1.01 if signal == "بيع" else 1)
    now = datetime.now(TIMEZONE).strftime('%Y-%m-%d %H:%M:%S')

    msg = format_message(symbol, close, signal, tp, sl, total_buy, total_sell,
                         last_vals['rsi'], last_vals['macd'], last_vals['macd_s'],
                         last_vals['st_k'], last_vals['st_d'], last_vals['bb_u'],
                         last_vals['bb_l'], last_vals['adx'], last_vals['psar'],
                         "\n".join(pattern_summary), now)

    send_telegram(msg)

def run_every_5_minutes():
    last_min = -1
    while True:
        now = datetime.now(TIMEZONE)
        if now.minute % 5 == 0 and now.minute != last_min and now.second < 10:
            last_min = now.minute
            try:
                for symbol in SYMBOLS:
                    analyze_symbol(symbol)
            except Exception:
                send_telegram(f"❌ توقف البوت بسبب خطأ:\n```{traceback.format_exc()}```")
        time.sleep(1)

# بدء التنفيذ
run_every_5_minutes()
