"""
自定义策略示例：包含关系匹配

使用方法：
1. 将此文件保存在 strategies/plugins/ 目录下
2. 重启服务（或等待自动热加载）
3. 在前端下拉框中选择 "contains"
"""

from ..base import EvaluationStrategy

class ContainsStrategy(EvaluationStrategy):
    """
    策略名称：包含关系匹配
    逻辑：只要实际结果包含预期结果（或反之），即视为通过
    场景：适用于接口返回内容较多，只需验证关键信息存在的场景
    """
    
    # 定义策略在前端显示的名称
    name = "contains"
    
    def get_display_name(self):
        return "包含关系匹配"
    
    def evaluate(self, expected, actual):
        """
        评测逻辑：
        1. 将输入转换为字符串
        2. 判断 expected 是否在 actual 中，或者 actual 是否在 expected 中
        """
        if expected is None or actual is None:
            return False
            
        exp_str = str(expected)
        act_str = str(actual)
        
        # 双向包含检查
        return exp_str in act_str or act_str in exp_str
