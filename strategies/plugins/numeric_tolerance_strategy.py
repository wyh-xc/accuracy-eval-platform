"""
数值容差匹配策略

适用于浮点数或数值比对，允许一定的误差范围。
"""

from ..base import EvaluationStrategy


class NumericToleranceStrategy(EvaluationStrategy):
    """
    策略名称：数值容差匹配
    逻辑：将预期值和实际值转换为数值后，判断差值是否在容差范围内
    场景：适用于浮点数计算结果比对、机器学习模型输出验证等
    """

    name = "numeric_tolerance"
    description = "数值容差：允许数值在一定误差范围内（默认容差 0.01）"
    
    def __init__(self, tolerance=0.01):
        """
        初始化数值容差策略
        
        参数:
            tolerance: 允许的误差范围，默认 0.01
        """
        self.tolerance = tolerance

    def get_display_name(self):
        return f"数值容差匹配 (±{self.tolerance})"

    def evaluate(self, expected, actual):
        """
        评测逻辑：
        1. 尝试将输入转换为浮点数
        2. 计算两者的绝对差值
        3. 判断差值是否在容差范围内
        """
        if expected is None or actual is None:
            return False
        
        try:
            exp_num = float(expected)
            act_num = float(actual)
            
            # 计算绝对差值
            diff = abs(exp_num - act_num)
            
            return diff <= self.tolerance
            
        except (ValueError, TypeError):
            # 无法转换为数值时，返回 False
            return False
