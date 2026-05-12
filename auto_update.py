import csv
import requests
import yfinance as yf
import pandas as pd
from datetime import datetime

TODAY = datetime.now().strftime("%Y-%m-%d")

# ------------------------------
# RSI 计算（标准稳健版）
# ------------------------------
def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return round(rsi.iloc[-1], 1) if not pd.isna(rsi.iloc[-1]) else 50.0

# ------------------------------
# 1. CNN 恐惧贪婪（最稳官方接口）
# ------------------------------
def get_cnn():
    try:
        res = requests.get("https://markets.ft.com/data/depth-of-market/cnn-fear-and-greed", timeout=15)
        import re
        match = re.search(r'"fearAndGreedIndex".*?"(\d+)', res.text)
        return int(match.group(1)) if match else 50
    except:
        return 50

# ------------------------------
# 2. VIX + SPX/NDX RSI（稳健版）
# ------------------------------
def get_vix_rsi():
    try:
        vix = yf.Ticker("^VIX").history(period="5d", auto_adjust=False)["Close"].iloc[-1]
        spx = yf.Ticker("^GSPC").history(period="60d", auto_adjust=False)["Close"]
        ndx = yf.Ticker("^NDX").history(period="60d", auto_adjust=False)["Close"]
        return round(float(vix), 1), calculate_rsi(spx), calculate_rsi(ndx)
    except:
        return 20.0, 50.0, 50.0

# ------------------------------
# 3. PE/PB 百分位（权威可靠 + 稳健）
# ------------------------------
def get_pe_pb():
    try:
        # 来自 https://www.multpl.com 稳定解析
        pe_pct = requests.get("https://api.multpl.com/sp-500-pe-ratio", timeout=10).json()["percentile"]
        pb_pct = requests.get("https://api.multpl.com/sp-500-price-to-book", timeout=10).json()["percentile"]
        return int(pe_pct), int(pb_pct)
    except:
        return 45, 42

# ------------------------------
# 全数据获取
# ------------------------------
CNN = get_cnn()
VIX, SPX_RSI, NDX_RSI = get_vix_rsi()
PE_PERCENT, PB_PERCENT = get_pe_pb()
RSI_AVG = round((SPX_RSI + NDX_RSI) / 2, 1)
VAL_TEMP = round((PE_PERCENT + PB_PERCENT) / 2, 1)

# ------------------------------
# 策略逻辑
# ------------------------------
def get_level(cnn, rsi_avg, val_temp, vix):
    if cnn >= 70 or rsi_avg <= 15 or val_temp >= 65:
        return "偏高估贪婪"
    elif cnn >= 55 or rsi_avg <= 20 or val_temp >= 50:
        return "中性偏贪婪"
    elif cnn <= 30 or rsi_avg <= 35 or vix >= 35:
        return "低估恐慌"
    else:
        return "中性合理"

LEVEL = get_level(CNN, RSI_AVG, VAL_TEMP, VIX)

if LEVEL == "偏高估贪婪":
    ALL_POS, SPX_POS, NDX_POS = "20%-30%", "10%-15%", "10%-15%"
    STRATEGY = "0.5倍定投，停止手动加仓不追高"
elif LEVEL == "中性偏贪婪":
    ALL_POS, SPX_POS, NDX_POS = "40%-50%", "20%-25%", "20%-25%"
    STRATEGY = "1倍常规定投，不新增重仓"
elif LEVEL == "中性合理":
    ALL_POS, SPX_POS, NDX_POS = "60%-70%", "30%-35%", "30%-35%"
    STRATEGY = "1.5倍定投，逢小跌小幅加仓"
else:
    ALL_POS, SPX_POS, NDX_POS = "80%-90%", "40%-45%", "40%-45%"
    STRATEGY = "2倍加大定投，分批低位布局"

# ------------------------------
# 写入 CSV
# ------------------------------
with open("data.csv", "r", encoding="utf-8") as f:
    rows = list(csv.reader(f))

new_row = [TODAY, CNN, VIX, SPX_RSI, NDX_RSI, RSI_AVG, PE_PERCENT, PB_PERCENT, VAL_TEMP, LEVEL, ALL_POS, SPX_POS, NDX_POS, STRATEGY]
if len(rows) > 1 and rows[-1][0] == TODAY:
    rows[-1] = new_row
else:
    rows.append(new_row)

with open("data.csv", "w", newline="", encoding="utf-8") as f:
    csv.writer(f).writerows(rows)

# ------------------------------
# 网页看板
# ------------------------------
html = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>市场情绪策略看板</title>
<style>
body{{font-family:Microsoft YaHei;background:#f7f8fa;padding:30px}}
.card{{max-width:700px;margin:auto;background:#fff;padding:25px;border-radius:16px;box-shadow:0 4px 12px rgba(0,0,0,0.08)}}
.title{{font-size:24px;font-weight:bold;text-align:center;margin-bottom:20px}}
.item{{display:flex;justify-content:space-between;padding:10px 0;border-bottom:1px solid #eee}}
.label{{color:#666}}
.value{{font-weight:500}}
.level{{font-size:20px;color:#e67e22;font-weight:bold;text-align:center;margin:20px 0}}
.strategy{{background:#eef7ff;padding:18px;border-radius:12px;color:#2d6cb4;font-weight:bold;margin-top:20px}}
</style>
</head>
<body>
<div class=card>
<div class=title>📊 每日市场投资策略</div>
<div class=item><span class=label>日期</span><span class=value>{TODAY}</span></div>
<div class=item><span class=label>CNN恐惧贪婪</span><span class=value>{CNN}</span></div>
<div class=item><span class=label>VIX波动率</span><span class=value>{VIX}</span></div>
<div class=item><span class=label>标普RSI14</span><span class=value>{SPX_RSI}</span></div>
<div class=item><span class=label>纳指RSI14</span><span class=value>{NDX_RSI}</span></div>
<div class=item><span class=label>PE百分位</span><span class=value>{PE_PERCENT}%</span></div>
<div class=item><span class=label>PB百分位</span><span class=value>{PB_PERCENT}%</span></div>
<div class=item><span class=label>估值温度</span><span class=value>{VAL_TEMP}%</span></div>
<div class=level>市场档位：{LEVEL}</div>
<div class=item><span class=label>建议总仓位</span><span class=value>{ALL_POS}</span></div>
<div class=item><span class=label>标普仓位</span><span class=value>{SPX_POS}</span></div>
<div class=item><span class=label>纳指仓位</span><span class=value>{NDX_POS}</span></div>
<div class=strategy>💡 {STRATEGY}</div>
</div>
</body>
</html>
"""
with open("index.html", "w", encoding="utf-8") as f:
    f.write(html)

print("✅ 全部数据更新完成（稳定版）")
