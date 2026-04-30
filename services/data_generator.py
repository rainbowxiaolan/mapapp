# services/data_generator.py
# 数据生成模块 —— 按省份人口占比生成百万级模拟微博数据，并与 mock 数据融合
# 缓存机制：同一天内同一话题只生成一次，0 点后重新生成（总量微幅上浮，情感浮动 ≤1%）

import os
import json
import random
import datetime
from typing import Dict, Any, List, Tuple

# ---------------------------------------------------------------------------
# 1. 省份人口数据（2025 年常住人口，单位：万人）
# ---------------------------------------------------------------------------
POPULATION_MILLIONS = {
    "广东": 12859, "山东": 10043, "河南": 9744, "江苏": 8518,
    "四川": 8318, "河北": 7354, "浙江": 6701, "湖南": 6492,
    "安徽": 6082, "湖北": 5811, "广西": 4989, "云南": 4644,
    "江西": 4474, "福建": 4190, "辽宁": 4131, "陕西": 3936,
    "贵州": 3857, "山西": 3424, "重庆": 3187, "黑龙江": 3001,
    "新疆": 2639, "上海": 2485, "甘肃": 2443, "内蒙古": 2374,
    "吉林": 2297, "北京": 2180, "天津": 1363, "海南": 1055,
    "宁夏": 732, "青海": 592, "西藏": 374,
    "台湾": 2330, "香港": 724, "澳门": 69,   # 港澳台占比很小，但保留
}

POP_TOTAL = sum(POPULATION_MILLIONS.values())

# 计算每个省份的人口占比（用于分配微博数量）
POP_RATIO = {prov: pop / POP_TOTAL for prov, pop in POPULATION_MILLIONS.items()}

# 缓存目录
CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "cache")


# ---------------------------------------------------------------------------
# 2. Mock 数据聚合（与现有情感分析、地理解析结果融合）
# ---------------------------------------------------------------------------
def _aggregate_mock_records(records: List[Dict[str, Any]]) -> Dict[str, Dict[str, int]]:
    """将带有情感标签和归一化省份的 mock 记录聚合成各省份情绪计数"""
    counts: Dict[str, Dict[str, int]] = {}
    for rec in records:
        prov = rec.get("normalized_location", "")
        label = rec.get("sentiment", {}).get("label", "neutral")
        if prov not in counts:
            counts[prov] = {"positive": 0, "negative": 0, "neutral": 0}
        if label in ("positive", "negative", "neutral"):
            counts[prov][label] += 1
        else:
            counts[prov]["neutral"] += 1
    return counts


# ---------------------------------------------------------------------------
# 3. 核心生成逻辑
# ---------------------------------------------------------------------------
def _generate_province_stats(topic: str,
                             mock_counts: Dict[str, Dict[str, int]]) -> Dict[str, Dict[str, Any]]:
    """
    根据话题生成全国各省份的情绪统计数据，并与 mock 数据融合。
    返回数据结构与 aggregator.aggregate_by_province 的输出一致。
    """
    # --- 3.1 全国总微博数（100万 ~ 500万 随机）---
    total_nation = random.randint(1_000_000, 5_000_000)

    # --- 3.2 按人口占比分配各省份总量 ---
    province_totals: Dict[str, int] = {}
    # 先按比例计算整数部分
    allocated = 0
    for prov in POP_RATIO:
        raw = int(total_nation * POP_RATIO[prov])
        province_totals[prov] = max(raw, 1)   # 保证每个省至少有 1 条
        allocated += province_totals[prov]

    # 余数按人口占比随机分配到各省（避免四舍五入导致总数不一致）
    remainder = total_nation - allocated
    if remainder > 0:
        provinces = list(POP_RATIO.keys())
        # 按人口占比作为权重随机选择省份
        weights = [POP_RATIO[p] for p in provinces]
        for _ in range(remainder):
            chosen = random.choices(provinces, weights=weights, k=1)[0]
            province_totals[chosen] += 1

    # --- 3.3 生成各省份正/负/中性数量 ---
    result: Dict[str, Dict[str, Any]] = {}
    for prov, total in province_totals.items():
        # 正向量在 [40%, 60%] 随机，负向量同理，剩余为中性
        pct_pos = random.uniform(0.40, 0.60)
        pct_neg = random.uniform(0.40, 0.60)
        # 保证 pct_pos + pct_neg ≤ 1.0，中性非负
        if pct_pos + pct_neg > 1.0:
            scale = 1.0 / (pct_pos + pct_neg)
            pct_pos *= scale
            pct_neg *= scale

        pos = int(total * pct_pos)
        neg = int(total * pct_neg)
        neu = total - pos - neg
        if neu < 0:
            neu = 0
            # 微调使总和等于 total
            if pos + neg > total:
                pos = int(total * 0.45)
                neg = total - pos - neu

        # 叠加上 mock 数据（微小平衡量）
        mock = mock_counts.get(prov, {})
        pos += mock.get("positive", 0)
        neg += mock.get("negative", 0)
        neu += mock.get("neutral", 0)
        # 叠加后重新计算 total
        total_merged = pos + neg + neu

        # 计算情绪指数
        if total_merged > 0:
            emotion_index = (pos - neg) / total_merged
        else:
            emotion_index = 0.0

        # 判定主导情绪
        if emotion_index > 0.2:
            dominant = "positive"
        elif emotion_index < -0.2:
            dominant = "negative"
        else:
            dominant = "neutral"

        result[prov] = {
            "positive": pos,
            "negative": neg,
            "neutral": neu,
            "total": total_merged,
            "emotion_index": round(emotion_index, 3),
            "dominant_emotion": dominant,
        }

    return result


# ---------------------------------------------------------------------------
# 4. 缓存读写
# ---------------------------------------------------------------------------
def _cache_path(topic: str) -> str:
    """返回话题对应的缓存文件路径（按天区分）"""
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR, exist_ok=True)

    today = datetime.date.today().isoformat()   # "2026-04-30"
    safe_topic = topic.replace("/", "_").replace("\\", "_")
    filename = f"{safe_topic}_{today}.json"
    return os.path.join(CACHE_DIR, filename)


def _load_cache(topic: str) -> Dict[str, Any] | None:
    """读取今天的缓存，若昨天的缓存存在则用于重新生成（0 点更新）"""
    path = _cache_path(topic)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    # 尝试读取昨天的缓存（用于 0 点重新生成）
    yesterday = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()
    filename = f"{topic.replace('/', '_').replace('\\\\', '_')}_{yesterday}.json"
    yesterday_path = os.path.join(CACHE_DIR, filename)
    if os.path.exists(yesterday_path):
        with open(yesterday_path, "r", encoding="utf-8") as f:
            return json.load(f)

    return None


def _save_cache(topic: str, data: Dict[str, Any]) -> None:
    path = _cache_path(topic)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ---------------------------------------------------------------------------
# 5. 重新生成逻辑（0 点后触发）
# ---------------------------------------------------------------------------
def _regenerate_from_cache(cached: Dict[str, Any]) -> Dict[str, Any]:
    """
    基于昨天的缓存数据进行重新生成：
    - 总数上浮 0.9% ~ 1.5%
    - 正 / 负 / 中性上下浮动不超过 ±1%
    """
    new_data = {}
    for prov, stats in cached.items():
        # 总数上浮
        factor = random.uniform(1.009, 1.015)
        new_total = int(stats["total"] * factor)

        # 各情绪值在原基础上浮动 ±1%
        pos = int(stats["positive"] * random.uniform(0.99, 1.01))
        neg = int(stats["negative"] * random.uniform(0.99, 1.01))
        neu = new_total - pos - neg
        if neu < 0:
            neu = 0
            # 微调
            pos = int(new_total * stats["positive"] / stats["total"]) if stats["total"] else 0
            neg = new_total - pos - neu

        # 重新计算情绪指数
        emotion_index = (pos - neg) / new_total if new_total > 0 else 0.0
        if emotion_index > 0.2:
            dominant = "positive"
        elif emotion_index < -0.2:
            dominant = "negative"
        else:
            dominant = "neutral"

        new_data[prov] = {
            "positive": pos,
            "negative": neg,
            "neutral": neu,
            "total": new_total,
            "emotion_index": round(emotion_index, 3),
            "dominant_emotion": dominant,
        }
    return new_data


# ---------------------------------------------------------------------------
# 6. 对外接口
# ---------------------------------------------------------------------------
def get_or_generate_stats(topic: str,
                          mock_records: List[Dict[str, Any]] | None = None) -> Dict[str, Dict[str, Any]]:
    """
    获取话题的省份情绪统计数据。
    - 若缓存中有今天的，直接返回；
    - 若缓存中有昨天的，基于昨天数据重新生成（0 点更新）；
    - 否则全新生成。
    """
    cached = _load_cache(topic)
    if cached:
        # 检查是否是今天的缓存
        today_str = datetime.date.today().isoformat()
        # _load_cache 可能返回昨天或今天的数据；简单判断：若缓存里包含日期信息，则比对
        # 这里直接用文件路径判断（_load_cache 优先返回今天的）
        path = _cache_path(topic)
        if os.path.exists(path):
            return cached
        # 否则是昨天的数据，需要重新生成
        new_data = _regenerate_from_cache(cached)
        _save_cache(topic, new_data)
        return new_data

    # 聚合 mock 数据
    mock_counts = _aggregate_mock_records(mock_records) if mock_records else {}

    # 生成全新数据
    generated = _generate_province_stats(topic, mock_counts)
    _save_cache(topic, generated)
    return generated


# ---------------------------------------------------------------------------
# 7. 辅助：确保所有 34 个省级行政区都在结果中
# ---------------------------------------------------------------------------
ALL_PROVINCES = [
    "北京", "天津", "上海", "重庆", "河北", "山西", "辽宁", "吉林", "黑龙江",
    "江苏", "浙江", "安徽", "福建", "江西", "山东", "河南", "湖北", "湖南",
    "广东", "海南", "四川", "贵州", "云南", "陕西", "甘肃", "青海", "台湾",
    "内蒙古", "广西", "西藏", "宁夏", "新疆", "香港", "澳门"
]


def ensure_all_provinces(stats: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """保证返回结果中 34 个省级行政区齐全，缺少的补默认中性值"""
    full = {}
    for prov in ALL_PROVINCES:
        if prov in stats:
            full[prov] = stats[prov]
        else:
            full[prov] = {
                "positive": 0, "negative": 0, "neutral": 0, "total": 0,
                "emotion_index": 0.0, "dominant_emotion": "neutral"
            }
    return full