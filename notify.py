import urllib.request
import urllib.parse
import json
import os

PUSHPLUS_TOKEN = os.environ.get("PUSHPLUS_TOKEN", "")

CURRENT = {
    "pe": 30.8,
    "fearGreed": 42,
    "maDeviation": -3.2,
    "rsi": 45,
    "drawdown": -8.5,
}

def score_pe(pe):
    if pe < 20: return 100
    if pe < 25: return 80
    if pe < 28: return 60
    if pe < 32: return 40
    if pe < 36: return 20
    return 0

def score_fear_greed(fg):
    if fg < 15: return 100
    if fg < 25: return 85
    if fg < 40: return 65
    if fg < 55: return 45
    if fg < 70: return 25
    return 5

def score_ma(dev):
    if dev < -15: return 100
    if dev < -10: return 85
    if dev < -5: return 65
    if dev < 0: return 50
    if dev < 5: return 35
    if dev < 10: return 15
    return 0

def score_rsi(rsi):
    if rsi < 25: return 100
    if rsi < 35: return 80
    if rsi < 45: return 60
    if rsi < 55: return 40
    if rsi < 65: return 25
    if rsi < 75: return 10
    return 0

def score_drawdown(dd):
    if dd < -30: return 100
    if dd < -20: return 85
    if dd < -10: return 65
    if dd < -5: return 45
    if dd < 0: return 30
    return 10


def get_composite_score():
    weights = {"pe": 0.3, "fg": 0.25, "ma": 0.2, "rsi": 0.15, "dd": 0.1}
    scores = {
        "pe": score_pe(CURRENT["pe"]),
        "fg": score_fear_greed(CURRENT["fearGreed"]),
        "ma": score_ma(CURRENT["maDeviation"]),
        "rsi": score_rsi(CURRENT["rsi"]),
        "dd": score_drawdown(CURRENT["drawdown"]),
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


def build_message(scores, total):
    mult = get_multiplier(total)
    base = int(os.environ.get("BASE_AMOUNT", "1000"))
    mult_num = float(mult.replace("x", "")) if "x" in mult else 0
    amount = round(base * mult_num) if mult_num > 0 else 0

    level = "适合加仓" if total >= 60 else "正常定投" if total >= 35 else "建议观望"

    msg = f"""<h2>纳斯达克定投日报</h2>
<h3>综合评分：{total}/100 — {level}</h3>
<table border="1" cellpadding="6" cellspacing="0" style="border-collapse:collapse;">
<tr><th>指标</th><th>当前值</th><th>得分</th></tr>
<tr><td>PE 估值</td><td>{CURRENT['pe']}</td><td>{scores['pe']}</td></tr>
<tr><td>恐惧贪婪指数</td><td>{CURRENT['fearGreed']}</td><td>{scores['fg']}</td></tr>
<tr><td>均线偏离度</td><td>{CURRENT['maDeviation']}%</td><td>{scores['ma']}</td></tr>
<tr><td>RSI(14)</td><td>{CURRENT['rsi']}</td><td>{scores['rsi']}</td></tr>
<tr><td>距前高回撤</td><td>{CURRENT['drawdown']}%</td><td>{scores['dd']}</td></tr>
</table>
<p><b>建议定投倍数：{mult}</b></p>
<p>建议本月定投金额：<b>{amount} 元</b>（基础 {base} 元 × {mult}）</p>
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
    scores, total = get_composite_score()
    print(f"综合评分: {total}")
    title = f"纳斯达克定投提醒 | 评分 {total}/100"
    content = build_message(scores, total)
    send_pushplus(title, content)
