# 地理位置解析模块
# 将用户属地信息映射为标准省份名称

import sys
import os
from typing import List, Dict, Any

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from utils.province_map import normalize_location, get_all_provinces


class GeoParser:
    """地理位置解析器"""

    def __init__(self):
        """初始化地理位置解析器"""
        self.valid_provinces = set(get_all_provinces())

    def parse_record_location(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """
        解析单条记录的地理位置

        Args:
            record: 微博记录，应包含'user_location'字段

        Returns:
            带有标准化地理位置的记录
        """
        if not isinstance(record, dict):
            return record

        location = record.get('user_location', '')
        normalized = normalize_location(location)

        result = record.copy()
        result['normalized_location'] = normalized

        return result

    def batch_parse_locations(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        批量解析记录的地理位置

        Args:
            records: 微博记录列表

        Returns:
            带有标准化地理位置的记录列表
        """
        return [self.parse_record_location(record) for record in records]

    def filter_valid_locations(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        过滤出地理位置有效的记录

        Args:
            records: 微博记录列表

        Returns:
            地理位置有效的记录列表
        """
        return [record for record in records
                if record.get('normalized_location') in self.valid_provinces]

    def get_location_stats(self, records: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        统计各省份的记录数量

        Args:
            records: 微博记录列表

        Returns:
            各省份记录数量统计
        """
        stats = {}

        for record in records:
            location = record.get('normalized_location')
            if location:
                stats[location] = stats.get(location, 0) + 1

        return stats


# 创建全局实例
_parser_instance = None


def get_parser() -> GeoParser:
    """获取地理位置解析器单例"""
    global _parser_instance
    if _parser_instance is None:
        _parser_instance = GeoParser()
    return _parser_instance


def parse_locations(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    批量解析记录的地理位置（便捷函数）

    Args:
        records: 微博记录列表

    Returns:
        带有标准化地理位置的记录列表
    """
    parser = get_parser()
    return parser.batch_parse_locations(records)
