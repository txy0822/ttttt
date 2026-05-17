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
    "vulnerability": "漏洞",
    "exploit": "利用/漏洞利用",
    "cybersecurity": "网络安全",
    "breach": "泄露/入侵",
    "encryption": "加密",
    "lawsuit": "诉讼",
    "settlement": "和解",
    "layoff": "裁员",
    "restructure": "重组",
    "allegedly": "据称",
    "compliance": "合规",
    "patent": "专利",
    "antitrust": "反垄断",
    "scrutiny": "审查",
    "unprecedented": "前所未有的",
    "significant": "重大的",
    "demonstrate": "展示/证明",
    "implement": "实施",
    "integrate": "整合",
    "emerging": "新兴的",
    "disrupt": "扰乱/颠覆",
    "surge": "激增",
    "decline": "下降",
    "unveil": "发布/揭幕",
    "launch": "推出/发射",
    "feature": "功能/特性",
    "privacy": "隐私",
    "surveillance": "监控",
    "controversy": "争议",
    "investigate": "调查",
    "announce": "宣布",
    "platform": "平台",
    "subscription": "订阅",
    "advertising": "广告",
    "engagement": "参与度/互动",
    "addiction": "成瘾",
    "misinformation": "虚假信息",
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
                    articles.append({"title": title, "content": desc[:800]})
            return articles
        except Exception as e:
            print(f"NewsData API 失败: {e}")

    # 备用：用多个 RSS 源抓取
    rss_feeds = [
        "https://feeds.arstechnica.com/arstechnica/technology-lab",
        "https://www.theverge.com/rss/index.xml",
        "https://techcrunch.com/feed/",
        "https://rss.nytimes.com/services/xml/rss/nyt/Technology.xml",
    ]
    articles = []
    for feed_url in rss_feeds:
        if len(articles) >= 6:
            break
        try:
            req = urllib.request.Request(feed_url, headers={"User-Agent": "Mozilla/5.0"})
            resp = urllib.request.urlopen(req, timeout=10, context=ssl_ctx)
            content = resp.read().decode()
            # 通用 RSS 解析：匹配 <title> 和 <description>
            items = re.findall(r"<item>(.*?)</item>", content, re.DOTALL)
            if not items:
                items = re.findall(r"<entry>(.*?)</entry>", content, re.DOTALL)
            for item in items[:4]:
                title = re.search(r"<title[^>]*>(.*?)</title>", item, re.DOTALL)
                desc = re.search(r"<description[^>]*>(.*?)</description>", item, re.DOTALL)
                if not desc:
                    desc = re.search(r"<summary[^>]*>(.*?)</summary>", item, re.DOTALL)
                if title:
                    t = re.sub(r"<!\[CDATA\[|\]\]>", "", title.group(1)).strip()
                    d = ""
                    if desc:
                        d = re.sub(r"<!\[CDATA\[|\]\]>", "", desc.group(1))
                        d = re.sub(r"<[^>]+>", "", d).strip()[:800]
                    if t and len(t) > 10:
                        articles.append({"title": t, "content": d})
                if len(articles) >= 6:
                    break
        except Exception as e:
            print(f"RSS {feed_url} 失败: {e}")
            continue

    return articles


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
        encoded = urllib.parse.quote(text[:800])
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
