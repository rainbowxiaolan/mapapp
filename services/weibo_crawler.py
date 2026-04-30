# services/weibo_crawler.py
# 微博实时采集模块

import logging

logger = logging.getLogger(__name__)


def get_weibo_data_by_topic(topic: str, max_count: int = 100) -> list:

    logger.info(f"[Crawler] 接收到采集请求，话题={topic}，最大条数={max_count}")
    logger.info("[Crawler] ")
    return []