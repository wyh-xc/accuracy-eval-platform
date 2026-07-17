"""
忽略大小写匹配策略

适用于不区分大小写的文本比对场景。
"""

from ..base import EvaluationStrategy


class CaseInsensitiveMatchStrategy(EvaluationStrategy):
    """
    策略名称：忽略大小写匹配
    逻辑：将预期值和实际值都转换为小写后进行比较
    场景：适用于英文文本比对，不关心大小写的场景
    """

    name = "case_insensitive"
    description = "忽略大小写：将文本转为小写后比较"

    def get_display_name(self):
        return "忽略大小写匹配"

    def evaluate(self, expected, actual):
        """
        评测逻辑：
        1. 将输入转换为字符串
        2. 统一转为小写
        3. 比较处理后的结果
        """
        if expected is None or actual is None:
            return False
        
        exp_str = str(expected).lower()
        act_str = str(actual).lower()
        
        return exp_str == act_str
