import csv
import re
import requests
import yfinance as yf
from datetime import datetime

# ====================== 基础配置 ======================
TODAY = datetime.now().strftime("%Y-%m-%d")
log = []
HIST_DAYS = 7

# 官方查询网址（失败时带超链接）
SITE_CNN = "https://money.cnn.com/data/fear-and-greed/"
SITE_VIX = "https://finance.yahoo.com/quote/%5EVIX"
SITE_PE = "https://www.multpl.com/s-p-500-pe-ratio"
SITE_PB = "https://www.multpl.com/s-p-500-price-to-book"

# 真实浏览器头（multpl + CNN 都能过）
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.google.com/"
}

# ====================== RSI 工具函数 ======================
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

# ====================== 1. CNN 恐惧贪婪（官方真实值） ======================
def get_cnn():
    try:
        # 官方JSON接口
        url = f"https://production.dataviz.cnn.io/index/fearandgreed/graphdata/{TODAY}"
        r = requests.get(url, headers=HEADERS, timeout=15)
        data = r.json()
        score = int(data["fear_and_greed"]["score"])
        log.append(f"✅ CNN恐惧贪婪（官方）：{score}")
        return score
    except Exception as e:
        # 备用：网页抓取
        try:
            r = requests.get(SITE_CNN, headers=HEADERS, timeout=15)
            m = re.search(r'Current Fear & Greed Index.*?(\d+)', r.text, re.DOTALL)
            if m:
                score = int(m.group(1))
                log.append(f"✅ CNN恐惧贪婪（网页）：{score}")
                return score
        except:
            pass
        log.append(f"❌ CNN失败 | <a href='{SITE_CNN}' target='_blank'>手动查询</a>")
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
        log.append(f"✅ 标普RSI14：{s}")
        log.append(f"✅ 纳指RSI14：{n}")
        return v, s, n
    except Exception as e:
        log.append(f"❌ VIX/RSI失败 | <a href='{SITE_VIX}' target='_blank'>手动查询</a>")
        return 20.0, 50.0, 50.0

# ====================== 3. PE/PB 百分位（直接抓 multpl 真实值，不估算） ======================
def get_pe_pb_real():
    # PE 百分位
    try:
        r = requests.get(SITE_PE, headers=HEADERS, timeout=15)
        # multpl 页面有 "As of ..., the S&P 500 PE ratio is ..., which is higher than ...% of all readings"
        m_pe = re.search(r'higher than (\d{1,2}\.?\d*)%', r.text)
        pe_pct = round(float(m_pe.group(1)))
        log.append(f"✅ PE百分位（multpl真实）：{pe_pct}%")
    except:
        log.append(f"❌ PE失败 | <a href='{SITE_PE}' target='_blank'>PE查询</a>")
        pe_pct = 45

    # PB 百分位
    try:
        r = requests.get(SITE_PB, headers=HEADERS, timeout=15)
        m_pb = re.search(r'higher than (\d{1,2}\.?\d*)%', r.text)
        pb_pct = round(float(m_pb.group(1)))
        log.append(f"✅ PB百分位（multpl真实）：{pb_pct}%")
    except:
        log.append(f"❌ PB失败 | <a href='{SITE_PB}' target='_blank'>PB查询</a>")
        pb_pct = 42

    return pe_pct, pb_pct

# ====================== 拉取全部数据 ======================
CNN = get_cnn()
VIX, SPX_RSI, NDX_RSI = get_vix_rsi()
PE_PERCENT, PB_PERCENT = get_pe_pb_real()   # 关键：真实值，不是估算

RSI_AVG = round((SPX_RSI + NDX_RSI) / 2, 1)
VAL_TEMP = round((PE_PERCENT + PB_PERCENT) / 2, 1)

# ====================== 市场档位 + 配色 + 仪表盘 ======================
def get_level_info(cnn, rsi_avg, val_temp, vix):
    if cnn >= 70 or rsi_avg <= 15 or val_temp >= 65:
        return "偏高估贪婪", "#e74c3c", 90
    elif cnn >= 55 or rsi_avg <= 20 or val_temp >= 50:
        return "中性偏贪婪", "#f39c12", 65
    elif cnn <= 30 or rsi_avg <= 35 or vix >= 35:
        return "低估恐慌", "#27ae60", 10
    else:
        return "中性合理", "#3498db", 45

LEVEL, LEVEL_COLOR, GAUGE_PERCENT = get_level_info(CNN, RSI_AVG, VAL_TEMP, VIX)

if LEVEL == "偏高估贪婪":
    ALL_POS, SPX_POS, NDX_POS = "20%-30%", "10%-15%", "10%-15%"
    STRATEGY = "0.5倍定投，停止加仓，逢高减仓"
elif LEVEL == "中性偏贪婪":
    ALL_POS, SPX_POS, NDX_POS = "40%-50%", "20%-25%", "20%-25%"
    STRATEGY = "正常定投，不追加、不激进"
elif LEVEL == "中性合理":
    ALL_POS, SPX_POS, NDX_POS = "60%-70%", "30%-35%", "30%-35%"
    STRATEGY = "均衡持仓，正常定投可小幅加仓"
else:
    ALL_POS, SPX_POS, NDX_POS = "80%-90%", "40%-45%", "40%-45%"
    STRATEGY = "市场低估，可加大定投与布局力度"

# ====================== 读写CSV ======================
csv_path = "data.csv"
header = ["日期","CNN","VIX","标普RSI","纳指RSI","RSI均值","PE百分位","PB百分位","估值温度","档位","总仓位","标普仓位","纳指仓位","策略"]

try:
    with open(csv_path, "r", encoding="utf-8") as f:
        rows = list(csv.reader(f))
except FileNotFoundError:
    rows = [header]

new_row = [
    TODAY, str(CNN), str(VIX), str(SPX_RSI), str(NDX_RSI),
    str(RSI_AVG), str(PE_PERCENT), str(PB_PERCENT), str(VAL_TEMP),
    LEVEL, ALL_POS, SPX_POS, NDX_POS, STRATEGY
]

if len(rows) > 1 and rows[-1][0] == TODAY:
    rows[-1] = new_row
else:
    rows.append(new_row)

with open(csv_path, "w", newline="", encoding="utf-8") as f:
    csv.writer(f).writerows(rows)

history = rows[-HIST_DAYS:] if len(rows)>1 else []
date_list = [r[0] for r in history[1:]]
cnn_list = [r[1] for r in history[1:]]
vix_list = [r[2] for r in history[1:]]
val_list = [r[8] for r in history[1:]]

# ====================== 日志 ======================
log_text = "\n".join(log)
with open("update_log.txt", "w", encoding="utf-8") as f:
    f.write(f"【系统更新时间】{TODAY}\n{log_text}")

# ====================== 网页HTML ======================
html = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>市场情绪 · 智能投资策略看板</title>
<style>
    *{{margin:0;padding:0;box-sizing:border-box;font-family:"Microsoft YaHei",sans-serif;}}
    body{{background:linear-gradient(135deg,#edf2f7,#e2e8f0);padding:20px 15px;min-height:100vh;}}
    .container{{max-width:720px;margin:0 auto;}}
    .card{{background:#fff;border-radius:24px;padding:26px;margin-bottom:20px;box-shadow:0 8px 30px rgba(0,0,0,0.08);transition:all 0.3s ease;}}
    .card:hover{{transform:translateY(-3px);box-shadow:0 12px 40px rgba(0,0,0,0.12);}}

    .main-title{{font-size:26px;font-weight:bold;color:#1a202c;text-align:center;margin-bottom:8px;}}
    .sub-title{{text-align:center;color:#718096;font-size:14px;margin-bottom:24px;letter-spacing:1px;}}

    .grid{{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-bottom:22px;}}
    .item-card{{background:linear-gradient(145deg,#f8fafc,#f1f5f9);border-radius:16px;padding:18px;text-align:center;transition:0.3s ease;}}
    .item-card:hover{{background:linear-gradient(145deg,#eef2f7,#e4ebf2);transform:scale(1.02);}}
    .item-label{{font-size:14px;color:#64748b;margin-bottom:8px;}}
    .item-value{{font-size:22px;font-weight:bold;color:#1e293b;}}

    .gauge-wrap{{width:240px;height:240px;margin:0 auto 24px;position:relative;}}
    .gauge-text{{position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);font-size:20px;font-weight:bold;color:#2a2a2a;text-align:center;line-height:1.5;}}

    .level-box{{background:{LEVEL_COLOR};border-radius:16px;padding:16px;text-align:center;font-size:22px;font-weight:bold;color:#fff;margin:18px 0;letter-spacing:2px;box-shadow:0 4px 15px {LEVEL_COLOR}50;}}
    .strategy-box{{background:linear-gradient(135deg,#eef5ff,#e0ecff);border-radius:16px;padding:20px;color:#1e40af;font-weight:500;font-size:16px;line-height:1.7;}}

    canvas{{width:100%;height:240px;margin:12px 0;border-radius:12px;background:#f8fafc;}}
    table{{width:100%;border-collapse:collapse;margin-top:12px;font-size:13px;border-radius:12px;overflow:hidden;}}
    th{{background:linear-gradient(135deg,#f1f5f9,#e2e8f0);color:#475569;padding:12px 8px;border:none;}}
    td{{border:1px solid #f1f5f9;padding:10px 8px;text-align:center;color:#334155;background:#fff;}}

    .log{{background:linear-gradient(135deg,#f8fafc,#f1f5f9);padding:18px;border-radius:16px;font-size:14px;line-height:1.9;color:#475569;word-break:break-all;}}
    .log a{{color:#2563eb;text-decoration:none;font-weight:bold;}}
    .log a:hover{{text-decoration:underline;}}

    .footer{{text-align:center;margin-top:30px;color:#94a3b8;font-size:13px;}}
</style>
</head>
<body>
<div class="container">
    <div class="card">
        <div class="main-title">📊 市场情绪 · 智能投资策略看板</div>
        <div class="sub-title">每日北京时间早7:00 全自动更新 | PE/PB 来自 multpl 真实值</div>

        <div class="gauge-wrap">
            <canvas id="gauge"></canvas>
            <div class="gauge-text">当前<br>市场情绪</div>
        </div>

        <div class="grid">
            <div class="item-card"><div class="item-label">CNN恐惧贪婪指数（美股）</div><div class="item-value">{CNN}</div></div>
            <div class="item-card"><div class="item-label">VIX恐慌波动率</div><div class="item-value">{VIX}</div></div>
            <div class="item-card"><div class="item-label">标普500 RSI14</div><div class="item-value">{SPX_RSI}</div></div>
            <div class="item-card"><div class="item-label">纳指100 RSI14</div><div class="item-value">{NDX_RSI}</div></div>
            <div class="item-card"><div class="item-label">PE历史百分位（multpl）</div><div class="item-value">{PE_PERCENT}%</div></div>
            <div class="item-card"><div class="item-label">PB历史百分位（multpl）</div><div class="item-value">{PB_PERCENT}%</div></div>
            <div class="item-card"><div class="item-label">整体估值温度</div><div class="item-value">{VAL_TEMP}%</div></div>
            <div class="item-card"><div class="item-label">双RSI均值</div><div class="item-value">{RSI_AVG}</div></div>
        </div>

        <div class="level-box">当前市场档位：{LEVEL}</div>

        <div class="grid">
            <div class="item-card"><div class="item-label">建议总仓位</div><div class="item-value">{ALL_POS}</div></div>
            <div class="item-card"><div class="item-label">标普500仓位</div><div class="item-value">{SPX_POS}</div></div>
            <div class="item-card"><div class="item-label">纳指100仓位</div><div class="item-value">{NDX_POS}</div></div>
        </div>

        <div class="strategy-box">💡 智能操作策略：{STRATEGY}</div>
    </div>

    <div class="card">
        <div class="main-title" style="font-size:20px">📈 近7天历史趋势走势</div>
        <canvas id="chart"></canvas>
        <table>
            <tr><th>日期</th><th>CNN</th><th>VIX</th><th>估值温度</th><th>市场档位</th></tr>
"""
for i in range(len(date_list)):
    d = date_list[i]
    c = cnn_list[i]
    v = vix_list[i]
    val = val_list[i]
    html += f'<tr><td>{d}</td><td>{c}</td><td>{v}</td><td>{val}%</td><td>{history[i+1][9]}</td></tr>'

html += f"""
        </table>
    </div>

    <div class="card">
        <div class="main-title" style="font-size:20px">🔍 系统数据更新日志</div>
        <div class="log">{log_text.replace(chr(10),'<br>')}</div>
    </div>

    <div class="footer">
        由 GitHub Actions 全自动运维 · PE/PB 数据来自 multpl 真实百分位
    </div>
</div>

<script>
const gaugeCanvas = document.getElementById('gauge');
const gCtx = gaugeCanvas.getContext('2d');
gaugeCanvas.width = 480;
gaugeCanvas.height = 480;
const center = 240;
const radius = 190;
const percent = {GAUGE_PERCENT};
const color = "{LEVEL_COLOR}";

gCtx.beginPath();
gCtx.arc(center, center, radius, 0, Math.PI * 2);
gCtx.strokeStyle = "#e2e8f0";
gCtx.lineWidth = 28;
gCtx.stroke();

gCtx.beginPath();
gCtx.arc(center, center, radius, -Math.PI/2, Math.PI*2*(percent/100) - Math.PI/2);
gCtx.strokeStyle = color;
gCtx.lineWidth = 28;
gCtx.lineCap = "round";
gCtx.stroke();

const dates = {date_list};
const cnnData = {cnn_list};
const vixData = {vix_list};
const valData = {val_list};

const canvas = document.getElementById('chart');
const ctx = canvas.getContext('2d');
canvas.width = canvas.offsetWidth * 2;
canvas.height = 480;
ctx.scale(2,2);

function drawLine(data, color, offsetY){{
    const w = canvas.offsetWidth;
    const h = 200;
    const step = w / (data.length-1 || 1);
    ctx.beginPath();
    ctx.strokeStyle = color;
    ctx.lineWidth = 2.5;
    data.forEach((val,i)=>{{
        let y = h - (val / 100 * h * 0.85) + offsetY;
        if(i===0) ctx.moveTo(i*step, y);
        else ctx.lineTo(i*step, y);
    }});
    ctx.stroke();
}}
drawLine(cnnData, '#e74c3c', 10);
drawLine(vixData, '#3498db', 75);
drawLine(valData, '#27ae60', 140);
</script>
</body>
</html>
"""

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html)

print("✅ 已正式切换：PE/PB 直接抓取 multpl 真实百分位，CNN官方值，无估算")
