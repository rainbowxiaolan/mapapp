# services/ai_summary.py
# AI 智能解读模块
# 模式：'api' 调用真实大模型，'rule' 使用规则模板生成摘要

import random
from typing import List, Dict, Any


# ----------------- 可配置参数 -----------------
AI_MODE = "glm-4.6v"          # 可选 "rule" 或 "api"
# 若使用 API 模式，请填写以下配置
API_KEY = "d187386771444c12ba1b0f0c0088b219.xHi04momHDrLjeGN"
API_URL = "https://open.bigmodel.cn/api/paas/v4"              # 如 OpenAI / 通义千问 / 百度 的 endpoint
# -------------------------------------------

def generate_ai_summary(topic: str, table_data: List[Dict[str, Any]],
                        mode: str = None) -> str:
    """
    生成 AI 分析摘要

    Args:
        topic: 话题名称
        table_data: 各省统计表格数据（已排序）
        mode: 覆盖全局 AI_MODE

    Returns:
        自然语言分析文字
    """
    if mode is None:
        mode = AI_MODE

    if mode == "api":
        return _api_summary(topic, table_data)
    else:
        return _rule_based_summary(topic, table_data)


def _rule_based_summary(topic: str, table_data: List[Dict[str, Any]]) -> str:
    """
    基于规则的文本摘要生成（无需联网）
    """
    if not table_data:
        return f"关于'{topic}'，当前暂无足够数据进行分析。"

    total_positive = sum(row['positive'] for row in table_data)
    total_negative = sum(row['negative'] for row in table_data)
    total_neutral = sum(row['neutral'] for row in table_data)
    total = total_positive + total_negative + total_neutral

    # 找出正向/负向最突出的省份
    top_positive = max(table_data, key=lambda x: x['positive'] / max(x['total'], 1))
    top_negative = max(table_data, key=lambda x: x['negative'] / max(x['total'], 1))

    # 整体情绪判定
    if total_positive > total_negative:
        overall = "正向"
    elif total_negative > total_positive:
        overall = "负向"
    else:
        overall = "中性"

    # 构造摘要
    templates = [
        f"本次话题'{topic}'整体呈现{overall}情绪，共涉及全国{len(table_data)}个省级行政区。"
        f"其中正向声音集中在{top_positive['province']}等地，"
        f"而{top_negative['province']}地区负向情绪占比相对较高，"
        f"可能与当地用户对事件的不同感受有关。"
        f"建议持续关注地区差异变化。",

        f"分析发现，在'{topic}'话题下，多数省份表现出{overall}态度。"
        f"{top_positive['province']}的正向评论比例领先全国，"
        f"而{top_negative['province']}的负向讨论较为集中。"
        f"整体情绪指数表明该话题在全国范围内呈现一定的区域分化。",

        f"通过大数据分析，'{topic}'在全国范围内共产生{total:,}条讨论，"
        f"整体情绪偏向{overall}。其中{top_positive['province']}正向比例最高，"
        f"{top_negative['province']}负向比例最高，区域差异明显。"
    ]
    return random.choice(templates)


def _api_summary(topic: str, table_data: List[Dict[str, Any]]) -> str:
    """
    调用真实大模型 API 生成摘要（示例框架，需填充具体接口）
    """
    if not API_KEY or not API_URL:
        return _rule_based_summary(topic, table_data)  # 自动降级为规则模式

    # 构造 Prompt
    prompt = _build_prompt(topic, table_data)

    # TODO: 发送 HTTP 请求调用 API
    # 示例（OpenAI 风格）：
    # import requests
    # response = requests.post(API_URL, json={
    #     "model": "gpt-3.5-turbo",
    #     "messages": [{"role": "user", "content": prompt}],
    #     "temperature": 0.7
    # }, headers={"Authorization": f"Bearer {API_KEY}"})
    # result = response.json()
    # return result["choices"][0]["message"]["content"]

    return _rule_based_summary(topic, table_data)  # 未实现时兜底


def _build_prompt(topic: str, table_data: List[Dict[str, Any]]) -> str:
    """
    构造发给大模型的提示词
    """
    top5 = table_data[:5] if len(table_data) >= 5 else table_data
    stats = "\n".join(
        f"- {row['province']}: 正向{row['positive']} 负向{row['negative']} 中性{row['neutral']} 总{row['total']} 情绪指数{row['emotion_index']}"
        for row in top5
    )

    prompt = (
        f"话题：'{topic}'\n"
        f"以下是中国各省份关于该话题的情绪统计（前5名）：\n"
        f"{stats}\n"
        f"请根据以上数据生成一段100-150字的分析摘要，"
        f"内容包括整体情绪判断、区域差异特点、可能的原因分析，语气客观专业。"
    )
    return prompt