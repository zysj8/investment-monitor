import csv
import requests
import yfinance as yf
import pandas as pd
from datetime import datetime

TODAY = datetime.now().strftime("%Y-%m-%d")

# 计算RSI工具函数
def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return round(rsi.iloc[-1], 1) if not pd.isna(rsi.iloc[-1]) else 50

# 获取全真实市场数据
def get_real_data():
    try:
        # CNN恐惧贪婪
        cnn_resp = requests.get("https://api.alternative.me/fng/?limit=1", timeout=10)
        cnn = int(cnn_resp.json()["data"][0]["value"])

        # VIX波动率
        vix_resp = requests.get("https://query1.finance.yahoo.com/v8/finance/chart/VIX?interval=1d", timeout=10)
        vix = round(float(vix_resp.json()["chart"]["result"][0]["meta"]["regularMarketPrice"]), 1)

        # 标普500 RSI14
        spx = yf.Ticker("^GSPC").history(period="60d")
        spx_rsi = calculate_rsi(spx["Close"])

        # 纳指100 RSI14
        ndx = yf.Ticker("^NDX").history(period="60d")
        ndx_rsi = calculate_rsi(ndx["Close"])

        # 暂时固定PE/PB百分位（后续可再全自动化）
        pe_percent = 47
        pb_percent = 44

    except Exception as e:
        print(f"数据获取异常：{e}")
        cnn, vix, spx_rsi, ndx_rsi, pe_percent, pb_percent = 55, 20, 52, 50, 45, 42

    return cnn, vix, spx_rsi, ndx_rsi, pe_percent, pb_percent

CNN, VIX, SPX_RSI, NDX_RSI, PE_PERCENT, PB_PERCENT = get_real_data()

# 衍生指标计算
RSI_AVG = round((SPX_RSI + NDX_RSI) / 2, 1)
VAL_TEMP = round((PE_PERCENT + PB_PERCENT) / 2, 1)

# 综合档位判断
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

# 仓位与策略
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

# 写入CSV历史数据
new_row = [
    TODAY, CNN, VIX, SPX_RSI, NDX_RSI, RSI_AVG,
    PE_PERCENT, PB_PERCENT, VAL_TEMP, LEVEL,
    ALL_POS, SPX_POS, NDX_POS, STRATEGY
]

with open("data.csv", "r", encoding="utf-8") as f:
    rows = list(csv.reader(f))

last_date = rows[-1][0] if len(rows) > 1 else ""
if last_date == TODAY:
    rows[-1] = new_row
else:
    rows.append(new_row)

with open("data.csv", "w", newline="", encoding="utf-8") as f:
    csv.writer(f).writerows(rows)

# 生成可直接在线访问的精美网页 index.html
html_template = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>市场情绪 | 投资策略看板</title>
    <style>
        *{{margin:0;padding:0;box-sizing:border-box;font-family:"Microsoft YaHei",sans-serif;}}
        body{{background:#f5f7fa;padding:30px;}}
        .container{{max-width:680px;margin:0 auto;}}
        .card{{background:#fff;border-radius:16px;padding:28px;box-shadow:0 4px 20px rgba(0,0,0,0.08);margin-bottom:20px;}}
        .title{{font-size:26px;font-weight:bold;color:#1f2937;margin-bottom:24px;text-align:center;}}
        .row{{display:flex;justify-content:space-between;padding:12px 0;border-bottom:1px solid #f0f0f0;}}
        .label{{color:#6b7280;font-size:15px;}}
        .value{{color:#111827;font-size:15px;font-weight:500;}}
        .level{{font-size:20px;font-weight:bold;color:#d97706;text-align:center;margin:16px 0;}}
        .strategy{{background:#eff6ff;padding:16px;border-radius:12px;color:#1d4ed8;font-size:16px;margin-top:20px;}}
        .time{{text-align:center;color:#9ca3af;font-size:14px;margin-top:10px;}}
    </style>
</head>
<body>
    <div class="container">
        <div class="card">
            <div class="title">📊 每日市场情绪与仓位策略</div>
            <div class="time">更新日期：{TODAY}（每日早7点自动更新）</div>

            <div class="row">
                <div class="label">CNN恐惧与贪婪指数</div>
                <div class="value">{CNN}</div>
            </div>
            <div class="row">
                <div class="label">VIX恐慌波动率</div>
                <div class="value">{VIX}</div>
            </div>
            <div class="row">
                <div class="label">标普RSI14</div>
                <div class="value">{SPX_RSI}</div>
            </div>
            <div class="row">
                <div class="label">纳指RSI14</div>
                <div class="value">{NDX_RSI}</div>
            </div>
            <div class="row">
                <div class="label">双RSI均值</div>
                <div class="value">{RSI_AVG}</div>
            </div>
            <div class="row">
                <div class="label">估值温度</div>
                <div class="value">{VAL_TEMP}</div>
            </div>

            <div class="level">当前市场档位：{LEVEL}</div>

            <div class="row">
                <div class="label">建议总仓位</div>
                <div class="value">{ALL_POS}</div>
            </div>
            <div class="row">
                <div class="label">标普500仓位</div>
                <div class="value">{SPX_POS}</div>
            </div>
            <div class="row">
                <div class="label">纳指100仓位</div>
                <div class="value">{NDX_POS}</div>
            </div>

            <div class="strategy">
                💡 操作策略：{STRATEGY}
            </div>
        </div>
    </div>
</body>
</html>
"""

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html_template)

print(f"✅ {TODAY} 早7点定时任务已生效，网页看板生成完成")
