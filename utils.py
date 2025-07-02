import numpy as np
from scipy.signal import argrelextrema

# تحويل القيمة إلى float بأمان
def safe_float(val):
    try:
        return float(val)
    except:
        return float(val.item())

# تحديد مستويات الدعم
def find_support_levels(df, order=5):
    idx = argrelextrema(df['Close'].values, np.less_equal, order=order)[0]
    return df['Close'].iloc[idx].values

# تحديد مستويات المقاومة
def find_resistance_levels(df, order=5):
    idx = argrelextrema(df['Close'].values, np.greater_equal, order=order)[0]
    return df['Close'].iloc[idx].values

# التحقق إذا كان السعر قريب من مستوى دعم أو مقاومة
def is_near_level(price, levels, threshold=0.005):
    return any(abs(price - level) / level < threshold for level in levels)

# تنسيق إشارة الشمعة (برايس أكشن) لإدراجها في الرسالة
def summarize_patterns(patterns):
    if not patterns:
        return "لا توجد شموع"
    return ' | '.join(patterns)
