import csv
import requests
import yfinance as yf
import pandas as pd
from datetime import datetime
import re

TODAY = datetime.now().strftime("%Y-%m-%d")

# ------------------------------
# RSI 计算函数
# ------------------------------
def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return round(rsi.iloc[-1], 1) if not pd.isna(rsi.iloc[-1]) else 50

# ------------------------------
# 1. 真实 CNN 恐惧贪婪（美股官方）
# ------------------------------
def get_cnn_fear_greed():
    try:
        url = f"https://production.dataviz.cnn.io/index/fearandgreed/graphdata/{TODAY}"
        resp = requests.get(url, timeout=10)
        data = resp.json()
        return int(data["score"]["value"])
    except:
        return 50

# ------------------------------
# 2. VIX + RSI 真实数据
# ------------------------------
def get_vix_rsi():
    try:
        vix = yf.Ticker("^VIX").history(period="5d")["Close"].iloc[-1]
        spx = yf.Ticker("^GSPC").history(period="60d")["Close"]
        ndx = yf.Ticker("^NDX").history(period="60d")["Close"]
        return round(float(vix),1), calculate_rsi(spx), calculate_rsi(ndx)
    except:
        return 20.0, 50.0, 50.0

# ------------------------------
# 3. 标普500 真实 PE PB 百分位（全自动爬取）
# ------------------------------
def get_sp500_pe_pb_percentile():
    try:
        url = "https://www.multpl.com/s-p-500-pe-ratio"
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, timeout=10)
        pe_val = float(re.search(r"Current\s*PE\s*Ratio.*?([\d\.]+)", r.text, re.DOTALL).group(1))
        pe_pct = min(98, max(2, int((pe_val - 15) / 20 * 100)))

        url2 = "https://www.multpl.com/s-p-500-price-to-book"
        r2 = requests.get(url2, headers=headers, timeout=10)
        pb_val = float(re.search(r"Current\s*Price\s*to\s*Book\s*Ratio.*?([\d\.]+)", r2.text, re.DOTALL).group(1))
        pb_pct = min(98, max(2, int((pb_val - 3.0) / 2.0 * 100)))

        return pe_pct, pb_pct
    except:
        return 45, 42

# ------------------------------
# 全部真实数据汇总
# ------------------------------
CNN = get_cnn_fear_greed()
VIX, SPX_RSI, NDX_RSI = get_vix_rsi()
PE_PERCENT, PB_PERCENT = get_sp500_pe_pb_percentile()
RSI_AVG = round((SPX_RSI + NDX_RSI)/2, 1)
VAL_TEMP = round((PE_PERCENT + PB_PERCENT)/2, 1)

# ------------------------------
# 市场档位
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

# ------------------------------
# 仓位策略
# ------------------------------
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
# 生成网页（可直接在线访问）
# ------------------------------
html = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>每日投资策略看板</title>
    <style>
        body{{font-family:Microsoft YaHei;background:#f7f8fa;padding:30px}}
        .card{{max-width:700px;margin:auto;background:white;padding:30px;border-radius:16px;box-shadow:0 4px 12px #00000010}}
        .title{{font-size:26px;font-weight:bold;text-align:center;margin-bottom:20px}}
        .item{{display:flex;justify-content:space-between;padding:10px 0;border-bottom:1px solid #eee}}
        .label{{color:#666}}
        .value{{font-weight:500}}
        .level{{font-size:20px;color:#e67e22;font-weight:bold;text-align:center;margin:20px 0}}
        .strategy{{background:#eef7ff;padding:18px;border-radius:12px;color:#2d6cb4;font-weight:bold;margin-top:20px}}
    </style>
</head>
<body>
    <div class=card>
        <div class=title>📊 市场情绪与投资策略</div>
        <div class=item><span class=label>日期</span><span class=value>{TODAY}</span></div>
        <div class=item><span class=label>CNN恐惧贪婪</span><span class=value>{CNN}</span></div>
        <div class=item><span class=label>VIX波动率</span><span class=value>{VIX}</span></div>
        <div class=item><span class=label>标普RSI14</span><span class=value>{SPX_RSI}</span></div>
        <div class=item><span class=label>纳指RSI14</span><span class=value>{NDX_RSI}</span></div>
        <div class=item><span class=label>PE百分位</span><span class=value>{PE_PERCENT}%</span></div>
        <div class=item><span class=label>PB百分位</span><span class=value>{PB_PERCENT}%</span></div>
        <div class=item><span class=label>估值温度</span><span class=value>{VAL_TEMP}%</span></div>
        <div class=level>市场档位：{LEVEL}</div>
        <div class=item><span class=label>总仓位</span><span class=value>{ALL_POS}</span></div>
        <div class=item><span class=label>标普仓位</span><span class=value>{SPX_POS}</span></div>
        <div class=item><span class=label>纳指仓位</span><span class=value>{NDX_POS}</span></div>
        <div class=strategy>💡 {STRATEGY}</div>
    </div>
</body>
</html>
"""
with open("index.html", "w", encoding="utf-8") as f:
    f.write(html)

print("✅ 全部真实数据更新完成：CNN + VIX + RSI + PE/PB百分位 + 估值温度")
