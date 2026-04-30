# 情感分析模块
# MVP阶段：基于情感词的规则分析
# 扩展点：可替换为百度AI接口或本地BERT模型

from typing import Dict, List, Any
import sys
import os

# 添加项目根目录到路径，以便导入utils模块
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from utils.sentiment_dict import (
    POSITIVE_WORDS,
    NEGATIVE_WORDS,
    NEGATION_WORDS,
    DEGREE_WORDS,
    get_sentiment_word_type,
    get_degree_weight
)


class SentimentAnalyzer:
    """情感分析器"""

    def __init__(self, method: str = "rule"):
        """
        初始化情感分析器

        Args:
            method: 分析方法，"rule"表示基于规则的方法
                    未来可扩展为"api"（百度AI）或"model"（本地模型）
        """
        self.method = method

    def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """
        分析单条文本的情感倾向

        Args:
            text: 待分析的文本

        Returns:
            情感分析结果，包含:
            - label: "positive", "negative", "neutral"
            - score: 情感得分（正数表示正向，负数表示负向）
            - confidence: 置信度（0-1之间）
        """
        if not text or not isinstance(text, str):
            return {
                'label': 'neutral',
                'score': 0,
                'confidence': 0.5
            }

        # MVP阶段：基于规则的简单情感分析
        if self.method == "rule":
            return self._rule_based_analysis(text)

        # 未来扩展点：API方式
        elif self.method == "api":
            return self._api_based_analysis(text)

        # 未来扩展点：本地模型方式
        elif self.method == "model":
            return self._model_based_analysis(text)

        else:
            raise ValueError(f"未知的情感分析方法: {self.method}")

    def _rule_based_analysis(self, text: str) -> Dict[str, Any]:
        """
        基于规则的情感分析（MVP实现）

        Args:
            text: 待分析的文本

        Returns:
            情感分析结果
        """
        score = 0
        positive_count = 0
        negative_count = 0
        total_words = 0

        # 简单分词（按空格和标点分割）
        # 注意：这里使用的是简单的空格分词，实际中文可能需要更复杂的分词
        # 但为了MVP阶段的简洁性，这里采用简单的字符匹配方式
        words = self._simple_tokenize(text)

        i = 0
        while i < len(words):
            word = words[i]

            # 检查是否为情感词
            word_type = get_sentiment_word_type(word)

            if word_type == "positive":
                # 检查前面是否有否定词或程度词
                weight = self._check_context(words, i)
                score += 1 * weight
                positive_count += 1
                total_words += 1

            elif word_type == "negative":
                # 检查前面是否有否定词或程度词
                weight = self._check_context(words, i)
                score -= 1 * weight
                negative_count += 1
                total_words += 1

            i += 1

        # 判定情感标签
        if score > 0.3:
            label = "positive"
        elif score < -0.3:
            label = "negative"
        else:
            label = "neutral"

        # 计算置信度（基于情感词数量）
        if total_words == 0:
            confidence = 0.5
        else:
            confidence = min(0.9, 0.5 + total_words * 0.05)

        return {
            'label': label,
            'score': score,
            'confidence': round(confidence, 2)
        }

    def _simple_tokenize(self, text: str) -> List[str]:
        """
        简单分词（MVP阶段实现）

        Args:
            text: 文本

        Returns:
            词列表
        """
        # 使用最简单的方法：逐个字符检查
        # 为了确保能匹配到情感词，我们返回文本中的所有2字符以上的组合
        # 以及所有单个字符（如果它们是情感词）

        words = []

        # 先添加所有2字符及以上的子串（用于匹配情感词）
        for i in range(len(text)):
            for j in range(i + 1, min(i + 4, len(text) + 1)):  # 最多3个字符的词
                word = text[i:j]
                if len(word) >= 1:
                    words.append(word)

        # 去重
        words = list(set(words))

        return words

    def _check_context(self, words: List[str], current_pos: int) -> float:
        """
        检查词语上下文，判断是否有否定词或程度词

        Args:
            words: 词列表
            current_pos: 当前词的位置

        Returns:
            权重（考虑否定和程度）
        """
        weight = 1.0

        # 检查前面是否有程度词
        if current_pos > 0:
            prev_word = words[current_pos - 1]
            if prev_word in DEGREE_WORDS:
                weight = get_degree_weight(prev_word)

        # 检查前面是否有否定词
        if current_pos > 0:
            prev_word = words[current_pos - 1]
            if prev_word in NEGATION_WORDS:
                weight = -weight

        return weight

    def batch_analyze_sentiment(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        批量分析微博记录的情感

        Args:
            records: 微博记录列表，每条记录应包含'content'字段

        Returns:
            带有情感分析结果的记录列表
        """
        results = []

        for record in records:
            if not isinstance(record, dict):
                results.append(record)
                continue

            content = record.get('content', '')
            sentiment_result = self.analyze_sentiment(content)

            # 将情感结果合并到记录中
            result = record.copy()
            result['sentiment'] = sentiment_result

            results.append(result)

        return results

    # ============================================================
    # 扩展点：百度AI接口实现
    # ============================================================
    def _api_based_analysis(self, text: str) -> Dict[str, Any]:
        """
        基于百度AI的情感分析（扩展实现）

        Args:
            text: 待分析的文本

        Returns:
            情感分析结果
        """
        # TODO: 实现百度AI接口调用
        # 示例代码：
        # from aip import AipNlp
        # client = AipNlp(APP_ID, API_KEY, SECRET_KEY)
        # result = client.sentimentClassify(text)
        # 解析result并返回标准格式

        # 临时返回中性结果
        return {
            'label': 'neutral',
            'score': 0,
            'confidence': 0.5
        }

    # ============================================================
    # 扩展点：本地BERT模型实现
    # ============================================================
    def _model_based_analysis(self, text: str) -> Dict[str, Any]:
        """
        基于本地BERT模型的情感分析（扩展实现）

        Args:
            text: 待分析的文本

        Returns:
            情感分析结果
        """
        # TODO: 实现本地BERT模型推理
        # 示例代码：
        # from transformers import pipeline
        # classifier = pipeline("sentiment-analysis", model="bert-base-chinese")
        # result = classifier(text)[0]
        # 转换为标准格式

        # 临时返回中性结果
        return {
            'label': 'neutral',
            'score': 0,
            'confidence': 0.5
        }


# 创建全局实例
_analyzer_instance = None


def get_analyzer(method: str = "rule") -> SentimentAnalyzer:
    """
    获取情感分析器单例

    Args:
        method: 分析方法

    Returns:
        情感分析器实例
    """
    global _analyzer_instance
    if _analyzer_instance is None:
        _analyzer_instance = SentimentAnalyzer(method=method)
    return _analyzer_instance


def analyze_sentiment(text: str) -> Dict[str, Any]:
    """
    分析单条文本的情感（便捷函数）

    Args:
        text: 待分析的文本

    Returns:
        情感分析结果
    """
    analyzer = get_analyzer()
    return analyzer.analyze_sentiment(text)


def batch_analyze_sentiment(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    批量分析微博记录的情感（便捷函数）

    Args:
        records: 微博记录列表

    Returns:
        带有情感分析结果的记录列表
    """
    analyzer = get_analyzer()
    return analyzer.batch_analyze_sentiment(records)
