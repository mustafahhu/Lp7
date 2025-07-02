import json
import requests
import traceback

# تحميل الإعدادات من ملف config.json
def load_config(path="config.json"):
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ فشل في تحميل ملف الإعدادات: {e}")
        return {}

# إرسال رسالة إلى جميع البوتات
def send_telegram_message(text, bots):
    for bot in bots:
        try:
            requests.post(
                f"https://api.telegram.org/bot{bot['token']}/sendMessage",
                data={
                    "chat_id": bot['chat_id'],
                    "text": text,
                    "parse_mode": "Markdown"
                }
            )
        except Exception as e:
            print(f"❌ فشل إرسال الرسالة إلى بوت: {e}")

# إرسال رسالة عند بداية البوت
def notify_start(bots):
    send_telegram_message("✅ تم تشغيل البوت بنجاح", bots)

# إرسال رسالة عند توقف البوت بسبب خطأ
def notify_error(bots, err_msg=None):
    error_text = f"❌ توقف البوت بسبب خطأ:\n```{traceback.format_exc()}```"
    if err_msg:
        error_text += f"\n📌 {err_msg}"
    send_telegram_message(error_text, bots)
