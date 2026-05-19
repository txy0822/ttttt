import json
import os
from datetime import datetime, timezone, timedelta


def check_stock_detail(ak, code):
    """检查单只股票的成交量趋势和均线形态"""
    try:
        df = ak.stock_zh_a_hist(symbol=code, period="daily", adjust="qfq")
        if df is None or len(df) < 20:
            return None

        df = df.tail(20)
        closes = df["收盘"].tolist()
        volumes = df["成交量"].tolist()

        # 条件5：近5天成交量趋势向上
        recent_vol = volumes[-5:]
        if recent_vol[-1] <= recent_vol[0] * 1.2:
            return None

        # 成交量忽高忽低则排除
        avg_vol = sum(recent_vol) / len(recent_vol)
        vol_std = (sum((v - avg_vol)**2 for v in recent_vol) / len(recent_vol)) ** 0.5
        if avg_vol > 0 and vol_std / avg_vol > 0.6:
            return None

        # 条件6：5日/10日/20日均线多头发散
        ma5 = sum(closes[-5:]) / 5
        ma10 = sum(closes[-10:]) / 10
        ma20 = sum(closes[-20:]) / 20

        if not (ma5 > ma10 > ma20):
            return None

        return f"MA5={ma5:.2f} > MA10={ma10:.2f} > MA20={ma20:.2f}"
    except Exception as e:
        return None


def get_candidates():
    import akshare as ak

    print("正在获取 A 股行情数据...")
    df = ak.stock_zh_a_spot_em()
    print(f"获取到 {len(df)} 只股票")
    print(f"列名: {list(df.columns)}")

    # 适配列名（akshare 不同版本列名可能不同）
    col_map = {}
    for col in df.columns:
        if "代码" in col: col_map["code"] = col
        elif "名称" in col: col_map["name"] = col
        elif "涨跌幅" in col: col_map["change_pct"] = col
        elif "量比" in col: col_map["volume_ratio"] = col
        elif "换手率" in col: col_map["turnover_rate"] = col
        elif "流通市值" in col: col_map["float_cap"] = col
        elif "最新价" in col: col_map["price"] = col

    required = ["code", "name", "change_pct", "volume_ratio", "turnover_rate", "float_cap", "price"]
    for key in required:
        if key not in col_map:
            print(f"缺少必要列: {key}")
            return []

    df = df.rename(columns={v: k for k, v in col_map.items()})

    # 转为数值类型
    for col in ["change_pct", "volume_ratio", "turnover_rate", "float_cap", "price"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=["change_pct", "volume_ratio", "turnover_rate", "float_cap"])

    # 条件1：涨幅 3-5%
    df = df[(df["change_pct"] >= 3) & (df["change_pct"] <= 5)]
    print(f"涨幅3-5%: {len(df)} 只")

    # 条件2：量比 > 1
    df = df[df["volume_ratio"] > 1]
    print(f"量比>1: {len(df)} 只")

    # 条件3：换手率 5-10%
    df = df[(df["turnover_rate"] >= 5) & (df["turnover_rate"] <= 10)]
    print(f"换手率5-10%: {len(df)} 只")

    # 条件4：流通市值 50-200亿
    df = df[(df["float_cap"] >= 50e8) & (df["float_cap"] <= 200e8)]
    print(f"流通市值50-200亿: {len(df)} 只")

    if df.empty:
        print("初步筛选后无符合条件的股票")
        return []

    # 条件5+6：逐只检查
    candidates = []
    for _, row in df.iterrows():
        code = row["code"]
        result = check_stock_detail(ak, code)
        if result:
            candidates.append({
                "code": code,
                "name": row["name"],
                "price": round(float(row["price"]), 2),
                "change_pct": round(float(row["change_pct"]), 2),
                "volume_ratio": round(float(row["volume_ratio"]), 2),
                "turnover_rate": round(float(row["turnover_rate"]), 2),
                "float_cap_yi": round(float(row["float_cap"]) / 1e8, 1),
                "ma_info": result
            })

    print(f"最终候选: {len(candidates)} 只")
    return candidates


if __name__ == "__main__":
    import pandas as pd
    import traceback
    bj = datetime.now(timezone(timedelta(hours=8)))

    try:
        candidates = get_candidates()
        output = {
            "date": bj.strftime("%Y-%m-%d"),
            "time": bj.strftime("%H:%M"),
            "count": len(candidates),
            "candidates": candidates
        }
    except Exception as e:
        error_msg = traceback.format_exc()
        print(f"运行出错:\n{error_msg}")
        output = {
            "date": bj.strftime("%Y-%m-%d"),
            "time": bj.strftime("%H:%M"),
            "count": 0,
            "candidates": [],
            "error": str(e),
            "traceback": error_msg
        }

    with open("stocks.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"stocks.json 已保存")
