# 数据聚合统计模块
# 按省份聚合统计情绪结果

from typing import List, Dict, Any
from collections import defaultdict


class SentimentAggregator:
    """情感数据聚合器"""

    def __init__(self):
        """初始化聚合器"""
        pass

    def aggregate_by_province(self, records: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """
        按省份聚合统计微博情绪数据

        Args:
            records: 微博记录列表，每条记录应包含:
                    - normalized_location: 标准化省份名称
                    - sentiment: 情感分析结果

        Returns:
            按省份聚合的统计数据，格式为:
            {
                "省份名": {
                    "positive": 正向数量,
                    "negative": 负向数量,
                    "neutral": 中性数量,
                    "total": 总数,
                    "emotion_index": 情绪指数,
                    "dominant_emotion": 主导情绪
                },
                ...
            }
        """
        # 按省份统计各情绪数量
        province_stats = defaultdict(lambda: {
            'positive': 0,
            'negative': 0,
            'neutral': 0
        })

        for record in records:
            if not isinstance(record, dict):
                continue

            province = record.get('normalized_location')
            if not province:
                continue

            sentiment = record.get('sentiment', {})
            label = sentiment.get('label', 'neutral')

            if label in ['positive', 'negative', 'neutral']:
                province_stats[province][label] += 1

        # 计算总数、情绪指数和主导情绪
        result = {}
        for province, stats in province_stats.items():
            total = stats['positive'] + stats['negative'] + stats['neutral']

            # 计算标准化情绪指数：(正向 - 负向) / 总数
            if total > 0:
                emotion_index = (stats['positive'] - stats['negative']) / total
            else:
                emotion_index = 0

            # 判定主导情绪
            if emotion_index > 0.2:
                dominant_emotion = 'positive'
            elif emotion_index < -0.2:
                dominant_emotion = 'negative'
            else:
                dominant_emotion = 'neutral'

            result[province] = {
                'positive': stats['positive'],
                'negative': stats['negative'],
                'neutral': stats['neutral'],
                'total': total,
                'emotion_index': round(emotion_index, 3),
                'dominant_emotion': dominant_emotion
            }

        return result

    def build_table_data(self, aggregated: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        构建适合表格展示的数据

        Args:
            aggregated: 聚合数据

        Returns:
            表格数据列表，按总数降序排序
        """
        table_data = []

        for province, stats in aggregated.items():
            row = {
                'province': province,
                'positive': stats['positive'],
                'negative': stats['negative'],
                'neutral': stats['neutral'],
                'total': stats['total'],
                'emotion_index': stats['emotion_index'],
                'dominant_emotion': stats['dominant_emotion']
            }
            table_data.append(row)

        # 按总数降序排序
        table_data.sort(key=lambda x: x['total'], reverse=True)

        return table_data

    def get_summary_stats(self, aggregated: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        获取汇总统计信息

        Args:
            aggregated: 聚合数据

        Returns:
            汇总统计信息
        """
        total_positive = sum(stats['positive'] for stats in aggregated.values())
        total_negative = sum(stats['negative'] for stats in aggregated.values())
        total_neutral = sum(stats['neutral'] for stats in aggregated.values())
        total_records = total_positive + total_negative + total_neutral

        # 计算整体情绪指数
        if total_records > 0:
            overall_emotion_index = (total_positive - total_negative) / total_records
        else:
            overall_emotion_index = 0

        # 判定整体主导情绪
        if overall_emotion_index > 0.2:
            overall_dominant = 'positive'
        elif overall_emotion_index < -0.2:
            overall_dominant = 'negative'
        else:
            overall_dominant = 'neutral'

        return {
            'total_records': total_records,
            'total_positive': total_positive,
            'total_negative': total_negative,
            'total_neutral': total_neutral,
            'overall_emotion_index': round(overall_emotion_index, 3),
            'overall_dominant_emotion': overall_dominant,
            'province_count': len(aggregated)
        }


# 创建全局实例
_aggregator_instance = None


def get_aggregator() -> SentimentAggregator:
    """获取聚合器单例"""
    global _aggregator_instance
    if _aggregator_instance is None:
        _aggregator_instance = SentimentAggregator()
    return _aggregator_instance


def aggregate_by_province(records: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """
    按省份聚合统计数据（便捷函数）

    Args:
        records: 微博记录列表

    Returns:
        聚合统计数据
    """
    aggregator = get_aggregator()
    return aggregator.aggregate_by_province(records)


def build_table_data(aggregated: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    构建表格数据（便捷函数）

    Args:
        aggregated: 聚合数据

    Returns:
        表格数据列表
    """
    aggregator = get_aggregator()
    return aggregator.build_table_data(aggregated)
