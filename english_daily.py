import urllib.request
import json
import ssl
import os
import re

ssl_ctx = ssl.create_default_context()
ssl_ctx.check_hostname = False
ssl_ctx.verify_mode = ssl.CERT_NONE

VOCAB_DICT = {
    "artificial intelligence": "人工智能",
    "machine learning": "机器学习",
    "neural network": "神经网络",
    "algorithm": "算法",
    "infrastructure": "基础设施",
    "semiconductor": "半导体",
    "revenue": "营收",
    "valuation": "估值",
    "acquisition": "收购",
    "deploy": "部署",
    "autonomous": "自主的",
    "leverage": "利用/杠杆",
    "scalable": "可扩展的",
    "disruption": "颠覆",
    "innovation": "创新",
    "regulatory": "监管的",
    "sustainable": "可持续的",
    "benchmark": "基准",
    "optimization": "优化",
    "latency": "延迟",
    "bandwidth": "带宽",
    "throughput": "吞吐量",
    "inference": "推理",
    "fine-tune": "微调",
    "open-source": "开源",
    "proprietary": "专有的",
    "monetize": "变现",
    "ecosystem": "生态系统",
    "volatility": "波动性",
    "bullish": "看涨的",
    "bearish": "看跌的",
    "rally": "反弹/上涨",
    "downturn": "下行/衰退",
    "portfolio": "投资组合",
    "dividend": "股息",
    "equity": "股权/权益",
    "hedge": "对冲",
    "surplus": "盈余",
    "deficit": "赤字",
}


def fetch_news():
    """从 NewsData.io 免费 API 获取科技新闻"""
    api_key = os.environ.get("NEWSDATA_KEY", "")
    if api_key:
        url = f"https://newsdata.io/api/1/latest?apikey={api_key}&category=technology&language=en&size=10"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        try:
            resp = urllib.request.urlopen(req, timeout=15, context=ssl_ctx)
            data = json.loads(resp.read().decode())
            articles = []
            for item in data.get("results", [])[:6]:
                title = item.get("title", "")
                desc = item.get("description", "") or ""
                if title:
                    articles.append({"title": title, "content": desc[:300]})
            return articles
        except Exception as e:
            print(f"NewsData API 失败: {e}")

    # 备用：用 RSS 抓取 TechCrunch
    try:
        url = "https://techcrunch.com/feed/"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        resp = urllib.request.urlopen(req, timeout=15, context=ssl_ctx)
        content = resp.read().decode()
        titles = re.findall(r"<title><!\[CDATA\[(.*?)\]\]></title>", content)
        descs = re.findall(r"<description><!\[CDATA\[(.*?)\]\]></description>", content)
        articles = []
        for i in range(min(6, len(titles))):
            desc = re.sub(r"<[^>]+>", "", descs[i]) if i < len(descs) else ""
            articles.append({"title": titles[i], "content": desc[:300]})
        return articles
    except Exception as e:
        print(f"RSS 备用方案也失败: {e}")
        return []


def find_vocab(text):
    """在文本中匹配词汇表中的词"""
    text_lower = text.lower()
    found = []
    for word, translation in VOCAB_DICT.items():
        if word in text_lower:
            found.append({"word": word, "meaning": translation})
    return found


def translate_text(text):
    """使用 MyMemory 免费 API 翻译英文到中文"""
    if not text.strip():
        return ""
    try:
        encoded = urllib.parse.quote(text[:500])
        url = f"https://api.mymemory.translated.net/get?q={encoded}&langpair=en|zh-CN"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        resp = urllib.request.urlopen(req, timeout=10, context=ssl_ctx)
        data = json.loads(resp.read().decode())
        return data["responseData"]["translatedText"]
    except Exception as e:
        print(f"翻译失败: {e}")
        return ""


def generate_daily():
    articles = fetch_news()
    if not articles:
        articles = [{
            "title": "AI continues to reshape the technology landscape",
            "content": "Major tech companies are investing heavily in artificial intelligence infrastructure, with semiconductor demand reaching new highs as data centers expand globally."
        }]

    # 翻译每篇文章
    for article in articles:
        article["titleZh"] = translate_text(article["title"])
        article["contentZh"] = translate_text(article["content"])

    # 提取词汇
    all_text = " ".join([a["title"] + " " + a["content"] for a in articles])
    vocab = find_vocab(all_text)

    from datetime import datetime, timezone, timedelta
    bj_time = datetime.now(timezone(timedelta(hours=8)))

    output = {
        "date": bj_time.strftime("%Y-%m-%d"),
        "articles": articles,
        "vocab": vocab[:10]
    }

    with open("english.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"english.json 已更新，{len(articles)} 篇文章，{len(vocab)} 个词汇")


if __name__ == "__main__":
    generate_daily()
