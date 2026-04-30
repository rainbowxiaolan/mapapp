# 数据清洗模块
# 用于对微博数据进行清洗和预处理

import re
from typing import List, Dict, Any


def clean_text(text: str) -> str:
    """
    清洗单条文本

    Args:
        text: 原始文本

    Returns:
        清洗后的文本
    """
    if not text or not isinstance(text, str):
        return ""

    # 去除首尾空白
    text = text.strip()

    # 去除多余空白字符（将连续空白替换为单个空格）
    text = re.sub(r'\s+', ' ', text)

    # 去除明显的无效字符（控制字符等）
    # 保留中文、英文、数字、常见标点
    text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)

    return text


def preprocess_records(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    预处理微博记录列表

    Args:
        records: 原始微博记录列表

    Returns:
        清洗后的微博记录列表
    """
    if not records:
        return []

    processed = []

    # 用于去重（基于内容）
    seen_contents = set()

    for record in records:
        # 验证记录必须有必要的字段
        if not isinstance(record, dict):
            continue

        # 清洗文本内容
        content = record.get('content', '')
        cleaned_content = clean_text(content)

        # 跳过空文本
        if not cleaned_content:
            continue

        # 去重（基于内容）
        if cleaned_content in seen_contents:
            continue
        seen_contents.add(cleaned_content)

        # 清洗其他字段
        processed_record = {
            'id': record.get('id'),
            'topic': record.get('topic', '').strip() if record.get('topic') else '',
            'content': cleaned_content,
            'user_location': record.get('user_location', '').strip() if record.get('user_location') else '',
            'created_at': record.get('created_at', '')
        }

        processed.append(processed_record)

    return processed


def validate_record(record: Dict[str, Any]) -> bool:
    """
    验证单条记录是否有效

    Args:
        record: 微博记录

    Returns:
        是否有效
    """
    if not isinstance(record, dict):
        return False

    # 检查必要字段
    if not record.get('content'):
        return False

    return True


def filter_by_location(records: List[Dict[str, Any]], valid_locations: set) -> List[Dict[str, Any]]:
    """
    根据有效地理位置过滤记录

    Args:
        records: 微博记录列表
        valid_locations: 有效的地理位置集合

    Returns:
        过滤后的记录列表
    """
    return [record for record in records
            if record.get('user_location') in valid_locations]
