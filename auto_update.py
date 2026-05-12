import csv
from datetime import datetime

# ===================== 【配置区】你可以改这里 =====================
# 模拟今日数据（后续我可以帮你接真实爬虫，现在先用自动生成演示）
TODAY = datetime.now().strftime("%Y-%m-%d")
CNN = 58          # 恐惧贪婪指数
VIX = 19          # 波动率指数
SPX_RSI = 56      # 标普RSI14
NDX_RSI = 53      # 纳指RSI14
PE_PERCENT = 46   # PE百分位
PB_PERCENT = 43   # PB百分位
# =================================================================

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

print(f"✅ {TODAY} 数据已自动更新完成！")
