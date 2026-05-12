import csv
import requests
import yfinance as yf
import pandas as pd
from datetime import datetime

# ====================== 基础配置 ======================
TODAY = datetime.now().strftime("%Y-%m-%d")
log = []

# ====================== 工具函数 ======================
def calculate_rsi(series, period=14):
    try:
        delta = series.diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        avg_gain = gain.rolling(window=period).mean()
        avg_loss = loss.rolling(window=period).mean()
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return round(rsi.iloc[-1], 1)
    except:
        return 50.0

# ====================== 1. CNN 恐惧贪婪 ======================
def get_cnn():
    try:
        r = requests.get("https://money.cnn.com/data/fear-and-greed/", timeout=10)
        import re
        s = re.search(r"Current\s*Score.*?(\d+)", r.text)
        val = int(s.group(1))
        log.append(f"✅ CNN恐惧贪婪：{val}")
        return val
    except:
        log.append("❌ CNN获取失败，使用50")
        return 50

# ====================== 2. VIX + RSI ======================
def get_vix_rsi():
    try:
        vix = yf.Ticker("^VIX").history(period="5d")["Close"].iloc[-1]
        spx = yf.Ticker("^GSPC").history(period="60d")["Close"]
        ndx = yf.Ticker("^NDX").history(period="60d")["Close"]
        v = round(float(vix), 1)
        s = calculate_rsi(spx)
        n = calculate_rsi(ndx)
        log.append(f"✅ VIX：{v}")
        log.append(f"✅ 标普RSI：{s}")
        log.append(f"✅ 纳指RSI：{n}")
        return v, s, n
    except:
        log.append("❌ VIX/RSI获取失败")
        return 20.0, 50.0, 50.0

# ====================== 3. PE/PB 百分位 ======================
def get_pe_pb():
    try:
        pe_pct = requests.get("https://api.multpl.com/sp-500-pe-ratio", timeout=10).json()["percentile"]
        pb_pct = requests.get("https://api.multpl.com/sp-500-price-to-book", timeout=10).json()["percentile"]
        p, b = int(pe_pct), int(pb_pct)
        log.append(f"✅ PE百分位：{p}%")
        log.append(f"✅ PB百分位：{b}%")
        return p, b
    except:
        log.append("❌ PE/PB获取失败")
        return 45, 42

# ====================== 执行获取 ======================
CNN = get_cnn()
VIX, SPX_RSI, NDX_RSI = get_vix_rsi()
PE_PERCENT, PB_PERCENT = get_pe_pb()

# 计算
RSI_AVG = round((SPX_RSI + NDX_RSI) / 2, 1)
VAL_TEMP = round((PE_PERCENT + PB_PERCENT) / 2, 1)

# ====================== 策略判断 ======================
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

# ====================== 写入CSV ======================
with open("data.csv", "r", encoding="utf-8") as f:
    rows = list(csv.reader(f))

new_row = [TODAY, CNN, VIX, SPX_RSI, NDX_RSI, RSI_AVG, PE_PERCENT, PB_PERCENT, VAL_TEMP, LEVEL, ALL_POS, SPX_POS, NDX_POS, STRATEGY]
if len(rows) > 1 and rows[-1][0] == TODAY:
    rows[-1] = new_row
else:
    rows.append(new_row)

with open("data.csv", "w", newline="", encoding="utf-8") as f:
    csv.writer(f).writerows(rows)

# ====================== 日志保存 ======================
log_text = "\n".join(log)
with open("update_log.txt", "w", encoding="utf-8") as f:
    f.write(f"【更新时间】{TODAY}\n{log_text}")

# ====================== 生成网页（带日志） ======================
html = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>市场情绪策略看板</title>
<style>
body{{font-family:Microsoft YaHei;background:#f7f8fa;padding:30px}}
.card{{max-width:700px;margin:auto;background:#fff;padding:25px;border-radius:16px;box-shadow:0 4px 12px rgba(0,0,0,0.08);margin-bottom:20px}}
.title{{font-size:24px;font-weight:bold;text-align:center;margin-bottom:20px}}
.item{{display:flex;justify-content:space-between;padding:10px 0;border-bottom:1px solid #eee}}
.label{{color:#666}}
.value{{font-weight:500}}
.level{{font-size:20px;color:#e67e22;font-weight:bold;text-align:center;margin:20px 0}}
.strategy{{background:#eef7ff;padding:18px;border-radius:12px;color:#2d6cb4;font-weight:bold;margin-top:20px}}
.log{{background:#f8f9fa;padding:15px;border-radius:10px;font-size:14px;line-height:1.6;color:#333;margin-top:10px}}
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

<div class=card>
<div class=title>🔍 数据更新日志</div>
<div class=log>{log_text.replace(chr(10),'<br>')}</div>
</div>

</body>
</html>
"""

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html)

print("✅ 全部数据更新完成，已生成日志 + 网页")
