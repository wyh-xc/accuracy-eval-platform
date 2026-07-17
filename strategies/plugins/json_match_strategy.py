"""
JSON 内容匹配策略

适用于比对 JSON 格式的数据，忽略字段顺序。
"""

import json
from ..base import EvaluationStrategy


class JSONMatchStrategy(EvaluationStrategy):
    """
    策略名称：JSON 内容匹配
    逻辑：将预期值和实际值解析为 JSON 对象后比较内容（忽略键顺序）
    场景：适用于 API 返回 JSON 数据的比对
    """

    name = "json_match"
    description = "JSON 匹配：解析 JSON 后比较内容，忽略字段顺序"

    def get_display_name(self):
        return "JSON 内容匹配"

    def evaluate(self, expected, actual):
        """
        评测逻辑：
        1. 尝试将输入解析为 JSON 对象
        2. 比较两个 JSON 对象的内容是否相等
        3. 支持嵌套的 JSON 结构
        """
        if expected is None or actual is None:
            return False
        
        try:
            # 如果已经是字典/列表，直接使用
            if isinstance(expected, (dict, list)):
                exp_obj = expected
            else:
                exp_obj = json.loads(str(expected))
            
            if isinstance(actual, (dict, list)):
                act_obj = actual
            else:
                act_obj = json.loads(str(actual))
            
            # 直接比较 Python 对象（会自动处理嵌套结构）
            return exp_obj == act_obj
            
        except (json.JSONDecodeError, TypeError, ValueError):
            # 无法解析为 JSON 时，返回 False
            return False
