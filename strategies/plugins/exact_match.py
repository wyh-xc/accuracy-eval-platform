"""
示例评测策略：精确匹配

此策略用于比较预期值和实际值是否完全相等（字符串形式）。
将此类文件放在 strategies/plugins 目录下，系统会自动加载。
"""

from strategies.base import EvaluationStrategy


class ExactMatchStrategy(EvaluationStrategy):
    """精确匹配策略：比较预期值和实际值的字符串形式是否完全相同。"""
    
    name = "exact_match"
    description = "精确匹配：预期值和实际值的字符串形式必须完全相同（包括大小写和空格）"
    
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
        
        # 转换为字符串并去除首尾空格后比较
        return str(expected).strip() == str(actual).strip()
