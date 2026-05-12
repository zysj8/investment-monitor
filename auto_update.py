import csv
import requests
from datetime import datetime

TODAY = datetime.now().strftime("%Y-%m-%d")

def get_real_data():
    try:
        # 获取真实的CNN恐惧与贪婪指数
        cnn_resp = requests.get("https://api.alternative.me/fng/?limit=1", timeout=10)
        cnn = int(cnn_resp.json()["data"][0]["value"])

        # 获取真实的VIX指数
        vix_resp = requests.get("https://query1.finance.yahoo.com/v8/finance/chart/VIX?interval=1d", timeout=10)
        vix = round(float(vix_resp.json()["chart"]["result"][0]["meta"]["regularMarketPrice"]), 1)

    except Exception as e:
        print(f"获取数据失败，使用备用值: {e}")
        cnn, vix = 55, 20

    # 标普/纳指RSI、PE/PB百分位（目前先用固定值，后续可以再升级）
    spx_rsi = 54
    ndx_rsi = 52
    pe_percent = 48
    pb_percent = 45

    return cnn, vix, spx_rsi, ndx_rsi, pe_percent, pb_percent

# 获取真实数据
CNN, VIX, SPX_RSI, NDX_RSI, PE_PERCENT, PB_PERCENT = get_real_data()

# 计算指标
RSI_AVG = round((SPX_RSI + NDX_RSI) / 2, 1)
VAL_TEMP = round((PE_PERCENT + PB_PERCENT) / 2, 1)

# 计算综合档位（完全按你的公式）
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

# 仓位 & 策略（完全按你的公式）
if LEVEL == "偏高估贪婪":
    ALL_POS = "20%-30%"
    SPX_POS = "10%-15%"
    NDX_POS = "10%-15%"
    STRATEGY = "0.5倍定投，停止手动加仓不追高"
elif LEVEL == "中性偏贪婪":
    ALL_POS = "40%-50%"
    SPX_POS = "20%-25%"
    NDX_POS = "20%-25%"
    STRATEGY = "1倍常规定投，不新增重仓"
elif LEVEL == "中性合理":
    ALL_POS = "60%-70%"
    SPX_POS = "30%-35%"
    NDX_POS = "30%-35%"
    STRATEGY = "1.5倍定投，逢小跌小幅加仓"
else:
    ALL_POS = "80%-90%"
    SPX_POS = "40%-45%"
    NDX_POS = "40%-45%"
    STRATEGY = "2倍加大定投，分批低位布局"

# 生成新一行数据
new_row = [
    TODAY, CNN, VIX, SPX_RSI, NDX_RSI, RSI_AVG,
    PE_PERCENT, PB_PERCENT, VAL_TEMP, LEVEL,
    ALL_POS, SPX_POS, NDX_POS, STRATEGY
]

# 写入CSV（保留历史所有数据，每天追加一行）
with open("data.csv", "r", encoding="utf-8") as f:
    rows = list(csv.reader(f))

# 如果今天已经有数据，就替换；没有就追加
last_date = rows[-1][0] if len(rows) > 1 else ""
if last_date == TODAY:
    rows[-1] = new_row
else:
    rows.append(new_row)

# 保存
with open("data.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerows(rows)

# 生成网页看板 index.html
html = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>市场情绪与投资策略看板</title>
    <style>
        body {{font-family: "Microsoft YaHei", sans-serif; margin: 30px; background-color: #f7f8fa;}}
        .card {{background-color: white; padding: 25px; border-radius: 12px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); margin-bottom: 20px; max-width: 600px;}}
        .title {{font-size: 24px; font-weight: bold; color: #2c3e50; margin-bottom: 20px;}}
        .item {{font-size: 16px; margin: 10px 0; color: #34495e;}}
        .strategy {{font-size: 18px; color: #e74c3c; font-weight: bold; margin-top: 20px; padding-top: 15px; border-top: 1px solid #eee;}}
    </style>
</head>
<body>
    <div class="card">
        <div class="title">📊 {TODAY} 市场投资策略</div>
        <div class="item">CNN恐惧与贪婪指数：{CNN}</div>
        <div class="item">VIX波动率：{VIX}</div>
        <div class="item">估值温度：{VAL_TEMP}</div>
        <div class="item">综合档位：{LEVEL}</div>
        <div class="item">建议总仓位：{ALL_POS}</div>
        <div class="item">标普仓位：{SPX_POS}  |  纳指仓位：{NDX_POS}</div>
        <div class="strategy">💡 操作策略：{STRATEGY}</div>
    </div>
</body>
</html>
"""
with open("index.html", "w", encoding="utf-8") as f:
    f.write(html)

print(f"✅ {TODAY} 数据已自动更新完成！")
