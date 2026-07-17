"""
示例评测策略：忽略大小写匹配

此策略用于比较预期值和实际值是否相等（忽略大小写）。
将此类文件放在 strategies/plugins 目录下，系统会自动加载。
"""

from strategies.base import EvaluationStrategy


class CaseInsensitiveMatchStrategy(EvaluationStrategy):
    """忽略大小写匹配策略：比较预期值和实际值的字符串形式是否相同（忽略大小写）。"""
    
    name = "case_insensitive"
    description = "忽略大小写匹配：预期值和实际值的字符串形式在忽略大小写后必须相同"
    
    def evaluate(self, expected, actual) -> bool:
        """
        评估实际值是否与预期值匹配。
        
        参数:
            expected: 数据集中的预期值
            actual: API 响应中的实际值
            
        返回:
            bool: 匹配返回 True，否则返回 False
        """
        if expected is None or actual is None:
            return False
        
        # 转换为小写字符串并去除首尾空格后比较
        return str(expected).strip().lower() == str(actual).strip().lower()
