import json
import os
import urllib.request
import ssl

PUSHPLUS_TOKEN = os.environ.get("PUSHPLUS_TOKEN", "")
BASE_AMOUNT = int(os.environ.get("BASE_AMOUNT", "1000"))

ssl_ctx = ssl.create_default_context()
ssl_ctx.check_hostname = False
ssl_ctx.verify_mode = ssl.CERT_NONE


def fetch_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        resp = urllib.request.urlopen(req, timeout=15, context=ssl_ctx)
        return json.loads(resp.read().decode())
    except Exception as e:
        print(f"请求失败 {url}: {e}")
        return None


def get_price_data():
    import yfinance as yf
    ticker = yf.Ticker("^NDX")
    hist = ticker.history(period="1y")
    if hist.empty:
        return None
    return hist["Close"].tolist()


def get_pe_ratio():
    import yfinance as yf
    ticker = yf.Ticker("QQQ")
    info = ticker.info
    pe = info.get("trailingPE")
    return round(pe, 1) if pe else None


def get_fear_greed():
    url = "https://production.dataviz.cnn.io/index/fearandgreed/graphdata"
    data = fetch_json(url)
    if data:
        try:
            return round(data["fear_and_greed"]["score"])
        except (KeyError, TypeError):
            pass
    url2 = "https://production.dataviz.cnn.io/index/fearandgreed/current"
    data2 = fetch_json(url2)
    if data2:
        try:
            return round(data2["fear_and_greed"]["score"])
        except (KeyError, TypeError):
            pass
    # 备用方案：用 VIX 反推恐惧贪婪值
    try:
        import yfinance as yf
        vix = yf.Ticker("^VIX")
        hist = vix.history(period="5d")
        if not hist.empty:
            vix_val = hist["Close"].iloc[-1]
            # VIX 越高越恐惧：VIX=10→贪婪90, VIX=30→恐惧20, VIX=50→极度恐惧5
            fg = max(0, min(100, round(100 - (vix_val - 10) * 2.25)))
            print(f"使用 VIX={vix_val:.1f} 估算恐惧贪婪指数={fg}")
            return fg
    except Exception as e:
        print(f"VIX 备用方案也失败: {e}")
    return None


def calc_rsi(closes, period=14):
    if len(closes) < period + 1:
        return None
    gains, losses = [], []
    for i in range(len(closes) - period, len(closes)):
        diff = closes[i] - closes[i - 1]
        gains.append(max(diff, 0))
        losses.append(max(-diff, 0))
    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period
    if avg_loss == 0:
        return 100
    rs = avg_gain / avg_loss
    return round(100 - (100 / (1 + rs)), 1)


def calc_ma_deviation(closes, period=200):
    if len(closes) < period:
        return None
    ma = sum(closes[-period:]) / period
    current = closes[-1]
    return round((current - ma) / ma * 100, 2)


def calc_drawdown(closes):
    if not closes:
        return None
    peak = max(closes)
    current = closes[-1]
    return round((current - peak) / peak * 100, 2)


def lerp(val, low, high, score_low, score_high):
    """线性插值：val 在 [low, high] 之间时，得分在 [score_high, score_low] 之间"""
    ratio = (val - low) / (high - low)
    return round(score_low + (score_high - score_low) * ratio)


def score_pe(pe):
    if pe is None: return 40
    if pe <= 18: return 100
    if pe <= 22: return lerp(pe, 18, 22, 100, 85)
    if pe <= 25: return lerp(pe, 22, 25, 85, 70)
    if pe <= 28: return lerp(pe, 25, 28, 70, 55)
    if pe <= 30: return lerp(pe, 28, 30, 55, 45)
    if pe <= 33: return lerp(pe, 30, 33, 45, 30)
    if pe <= 36: return lerp(pe, 33, 36, 30, 15)
    if pe <= 40: return lerp(pe, 36, 40, 15, 5)
    return 0

def score_fear_greed(fg):
    if fg is None: return 40
    if fg <= 10: return 100
    if fg <= 20: return lerp(fg, 10, 20, 100, 85)
    if fg <= 30: return lerp(fg, 20, 30, 85, 70)
    if fg <= 40: return lerp(fg, 30, 40, 70, 55)
    if fg <= 50: return lerp(fg, 40, 50, 55, 45)
    if fg <= 60: return lerp(fg, 50, 60, 45, 30)
    if fg <= 75: return lerp(fg, 60, 75, 30, 15)
    if fg <= 90: return lerp(fg, 75, 90, 15, 5)
    return 0

def score_ma(dev):
    if dev is None: return 40
    if dev <= -20: return 100
    if dev <= -15: return lerp(dev, -20, -15, 100, 90)
    if dev <= -10: return lerp(dev, -15, -10, 90, 75)
    if dev <= -5: return lerp(dev, -10, -5, 75, 60)
    if dev <= 0: return lerp(dev, -5, 0, 60, 45)
    if dev <= 5: return lerp(dev, 0, 5, 45, 30)
    if dev <= 10: return lerp(dev, 5, 10, 30, 15)
    if dev <= 15: return lerp(dev, 10, 15, 15, 5)
    return 0

def score_rsi(rsi):
    if rsi is None: return 40
    if rsi <= 20: return 100
    if rsi <= 30: return lerp(rsi, 20, 30, 100, 85)
    if rsi <= 40: return lerp(rsi, 30, 40, 85, 65)
    if rsi <= 50: return lerp(rsi, 40, 50, 65, 45)
    if rsi <= 60: return lerp(rsi, 50, 60, 45, 30)
    if rsi <= 70: return lerp(rsi, 60, 70, 30, 15)
    if rsi <= 80: return lerp(rsi, 70, 80, 15, 5)
    return 0

def score_drawdown(dd):
    if dd is None: return 40
    if dd <= -35: return 100
    if dd <= -25: return lerp(dd, -35, -25, 100, 90)
    if dd <= -15: return lerp(dd, -25, -15, 90, 70)
    if dd <= -10: return lerp(dd, -15, -10, 70, 55)
    if dd <= -5: return lerp(dd, -10, -5, 55, 40)
    if dd <= 0: return lerp(dd, -5, 0, 40, 20)
    return 5


def get_composite_score(pe, fg, ma, rsi, dd):
    weights = {"pe": 0.3, "fg": 0.25, "ma": 0.2, "rsi": 0.15, "dd": 0.1}
    scores = {
        "pe": score_pe(pe),
        "fg": score_fear_greed(fg),
        "ma": score_ma(ma),
        "rsi": score_rsi(rsi),
        "dd": score_drawdown(dd),
    }
    total = round(
        scores["pe"] * weights["pe"] + scores["fg"] * weights["fg"] +
        scores["ma"] * weights["ma"] + scores["rsi"] * weights["rsi"] +
        scores["dd"] * weights["dd"]
    )
    return scores, total


def get_multiplier(score):
    if score >= 80: return "3x"
    if score >= 65: return "2x"
    if score >= 50: return "1.5x"
    if score >= 35: return "1x"
    if score >= 20: return "0.5x"
    return "暂停"


def build_message(pe, fg, ma, rsi, dd, scores, total):
    mult = get_multiplier(total)
    mult_num = float(mult.replace("x", "")) if "x" in mult else 0
    amount = round(BASE_AMOUNT * mult_num) if mult_num > 0 else 0
    level = "适合加仓" if total >= 60 else "正常定投" if total >= 35 else "建议观望"
    def fmt(val, suffix=""):
        return f"{val}{suffix}" if val is not None else "获取失败"
    msg = f"""<h2>纳斯达克定投日报</h2>
<h3>综合评分：{total}/100 — {level}</h3>
<table border="1" cellpadding="6" cellspacing="0" style="border-collapse:collapse;">
<tr><th>指标</th><th>当前值</th><th>得分</th></tr>
<tr><td>PE 估值</td><td>{fmt(pe)}</td><td>{scores['pe']}</td></tr>
<tr><td>恐惧贪婪指数</td><td>{fmt(fg)}</td><td>{scores['fg']}</td></tr>
<tr><td>均线偏离度</td><td>{fmt(ma, '%')}</td><td>{scores['ma']}</td></tr>
<tr><td>RSI(14)</td><td>{fmt(rsi)}</td><td>{scores['rsi']}</td></tr>
<tr><td>距前高回撤</td><td>{fmt(dd, '%')}</td><td>{scores['dd']}</td></tr>
</table>
<p><b>建议定投倍数：{mult}</b></p>
<p>建议本月定投金额：<b>{amount} 元</b>（基础 {BASE_AMOUNT} 元 × {mult}）</p>
"""
    return msg


def send_pushplus(title, content):
    if not PUSHPLUS_TOKEN:
        print("未设置 PUSHPLUS_TOKEN，跳过推送")
        return
    data = json.dumps({
        "token": PUSHPLUS_TOKEN,
        "title": title,
        "content": content,
        "template": "html"
    }).encode("utf-8")
    req = urllib.request.Request(
        "http://www.pushplus.plus/send",
        data=data,
        headers={"Content-Type": "application/json"}
    )
    resp = urllib.request.urlopen(req)
    result = json.loads(resp.read().decode())
    print(f"推送结果: {result}")


if __name__ == "__main__":
    print("正在获取实时数据...")

    closes = get_price_data()
    pe = get_pe_ratio()
    fg = get_fear_greed()
    rsi = calc_rsi(closes) if closes else None
    ma = calc_ma_deviation(closes) if closes else None
    dd = calc_drawdown(closes) if closes else None

    print(f"PE={pe}, 恐惧贪婪={fg}, 均线偏离={ma}%, RSI={rsi}, 回撤={dd}%")

    scores, total = get_composite_score(pe, fg, ma, rsi, dd)
    print(f"综合评分: {total}/100")

    title = f"纳斯达克定投提醒 | 评分 {total}/100"
    content = build_message(pe, fg, ma, rsi, dd, scores, total)
    send_pushplus(title, content)

