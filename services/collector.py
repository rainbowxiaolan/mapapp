# 数据采集模块
# 支持mock数据和真实爬虫两种模式

import json
import os
from typing import List, Dict, Any

# 导入爬虫模块
try:
    from .weibo_crawler import get_weibo_data_by_topic as get_real_weibo_data
except ImportError:
    get_real_weibo_data = None


class WeiboDataCollector:
    """微博数据采集器 - 支持mock和真实数据"""

    def __init__(self, data_file: str = None, use_real_crawler: bool = False):
        """
        初始化数据采集器

        Args:
            data_file: 数据文件路径，默认为data/mock_weibo_data.json
            use_real_crawler: 是否使用真实爬虫（False则使用mock数据）
        """
        self.use_real_crawler = use_real_crawler

        if data_file is None:
            # 获取项目根目录
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            data_file = os.path.join(project_root, 'data', 'mock_weibo_data.json')

        self.data_file = data_file
        self._data_cache = None

    def _load_data(self) -> List[Dict[str, Any]]:
        """加载数据文件"""
        if self._data_cache is not None:
            return self._data_cache

        if not os.path.exists(self.data_file):
            raise FileNotFoundError(f"数据文件不存在: {self.data_file}")

        with open(self.data_file, 'r', encoding='utf-8') as f:
            self._data_cache = json.load(f)

        return self._data_cache

    def get_weibo_data_by_topic(self, topic: str) -> List[Dict[str, Any]]:
        """
        根据话题获取微博数据

        Args:
            topic: 话题关键词

        Returns:
            微博数据列表
        """
        all_data = self._load_data()

        # 精确匹配话题
        exact_matches = [item for item in all_data if item.get('topic') == topic]

        # 如果有精确匹配，返回匹配结果
        if exact_matches:
            return exact_matches

        # 如果没有精确匹配，尝试包含匹配
        fuzzy_matches = [item for item in all_data
                        if topic.lower() in item.get('topic', '').lower()]

        if fuzzy_matches:
            return fuzzy_matches

        # 如果都没有匹配，返回空列表
        # 也可以选择返回一些默认样本数据用于演示
        return []

    def get_all_topics(self) -> List[str]:
        """
        获取所有可用的话题列表

        Returns:
            话题列表（去重）
        """
        all_data = self._load_data()
        topics = list(set(item.get('topic', '') for item in all_data if item.get('topic')))
        return sorted(topics)

    def get_random_sample(self, count: int = 10) -> List[Dict[str, Any]]:
        """
        获取随机样本数据（用于演示）

        Args:
            count: 样本数量

        Returns:
            随机样本列表
        """
        import random
        all_data = self._load_data()
        return random.sample(all_data, min(count, len(all_data)))


# 创建全局实例
_collector_instance = None


def get_collector() -> WeiboDataCollector:
    """获取数据采集器单例"""
    global _collector_instance
    if _collector_instance is None:
        _collector_instance = WeiboDataCollector()
    return _collector_instance


def get_weibo_data_by_topic(topic: str, use_real: bool = None) -> List[Dict[str, Any]]:
    """
    根据话题获取微博数据（便捷函数）

    Args:
        topic: 话题关键词
        use_real: 是否使用真实爬虫（None则使用collector的默认设置）

    Returns:
        微博数据列表
    """
    if use_real is None:
        use_real = get_collector().use_real_crawler

    if use_real:
        # 使用真实爬虫
        return get_real_weibo_data(topic)
    else:
        # 使用mock数据
        collector = get_collector()
        return collector.get_weibo_data_by_topic(topic)


# ============================================================
# 扩展点说明：
# ============================================================
# 如果需要接入真实微博API，可以按照以下方式修改：
#
# class RealWeiboDataCollector(WeiboDataCollector):
#     """真实微博API数据采集器"""
#
#     def __init__(self, api_key: str, api_secret: str):
#         self.api_key = api_key
#         self.api_secret = api_secret
#         # 初始化API客户端
#
#     def get_weibo_data_by_topic(self, topic: str) -> List[Dict[str, Any]]:
#         # 调用真实微博API获取数据
#         # 将API返回的数据转换为标准格式
#         # 返回数据列表
#         pass
#
# 然后在代码中替换实例化方式即可：
# collector = RealWeiboDataCollector(api_key, api_secret)
# ============================================================
