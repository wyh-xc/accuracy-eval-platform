"""
精确匹配策略

这是最基础的评测策略：只有当预期结果和实际结果完全一致时才算通过。
"""

from ..base import EvaluationStrategy


class ExactMatchStrategy(EvaluationStrategy):
    """
    策略名称：精确匹配
    逻辑：预期值和实际值必须完全相同（包括大小写、空格等）
    场景：适用于对结果要求严格的场景，如ID匹配、代码比对等
    """

    name = "exact_match"
    description = "精确匹配：预期值和实际值必须完全相同"

    def get_display_name(self):
        return "精确匹配"

    def evaluate(self, expected, actual):
        """
        评测逻辑：
        1. 直接比较两个值是否相等
        2. None 值视为不相等
        """
        if expected is None or actual is None:
            return False
        
        # 直接比较，区分大小写和类型
        return expected == actual
