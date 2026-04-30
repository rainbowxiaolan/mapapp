# 系统配置文件

# 数据源配置
DATA_SOURCE = {
    'MODE': 'mock',  # 可选：'mock' 或 'crawler'
    'CRAWLER_ENABLED': False,  # 是否启用爬虫
    'CACHE_EXPIRE': 3600,  # 缓存过期时间（秒）
}

# 爬虫配置
CRAWLER_CONFIG = {
    'REQUEST_DELAY': 2,  # 请求间隔（秒）
    'MAX_RETRIES': 3,  # 最大重试次数
    'TIMEOUT': 10,  # 请求超时时间（秒）
    'USER_AGENT_ROTATION': True,  # 是否轮换User-Agent
}

# 分析配置
ANALYSIS_CONFIG = {
    'SENTIMENT_THRESHOLD': 0.3,  # 情感分析阈值
    'MIN_TEXT_LENGTH': 5,  # 最小文本长度
    'MAX_PROVINCE_NAME_LENGTH': 20,  # 最大省份名称长度
}

# 页面配置
PAGE_CONFIG = {
    'TITLE': '微博热点话题情绪地图',
    'SUBTITLE': '基于情感分析的地理可视化系统',
    'TOPIC_SUGGESTIONS': ['春节', '世界杯', '高考', '双11', '旅游'],
    'ENABLE_LOADING_ANIMATION': True,
}

def get_config(key: str = None):
    """
    获取配置值

    Args:
        key: 配置键，如果为None则返回所有配置

    Returns:
        配置值
    """
    if key:
        # 如果key包含点号，表示嵌套配置
        if '.' in key:
            section, subkey = key.split('.', 1)
            return eval(f'{section.upper()}_CONFIG')['{subkey}']
        else:
            return eval(f'{key.upper()}')
    else:
        # 返回所有配置
        return {
            'DATA_SOURCE': DATA_SOURCE,
            'CRAWLER_CONFIG': CRAWLER_CONFIG,
            'ANALYSIS_CONFIG': ANALYSIS_CONFIG,
            'PAGE_CONFIG': PAGE_CONFIG,
        }