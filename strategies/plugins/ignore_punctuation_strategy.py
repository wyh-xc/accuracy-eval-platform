"""
自定义策略示例：忽略标点符号的匹配

使用方法：
1. 将此文件保存在 strategies/plugins/ 目录下
2. 重启服务（或等待自动热加载）
3. 在前端下拉框中选择 "ignore_punctuation"
"""

import re
from ..base import EvaluationStrategy

class IgnorePunctuationStrategy(EvaluationStrategy):
    """
    策略名称：忽略标点符号匹配
    逻辑：去除所有标点符号和空格后进行比较
    """
    
    # 定义策略在前端显示的名称
    name = "ignore_punctuation"
    description = "忽略标点：去除标点和空格后比较文本内容"
    
    def get_display_name(self):
        return "忽略标点符号匹配"
    
    def evaluate(self, expected, actual):
        """
        评测逻辑：
        1. 将输入转换为字符串
        2. 移除所有非字母数字字符
        3. 比较处理后的结果
        """
        if expected is None or actual is None:
            return False
            
        # 转换为字符串并转小写
        exp_str = str(expected).lower()
        act_str = str(actual).lower()
        
        # 移除标点符号和空格 (只保留字母和数字)
        exp_clean = re.sub(r'[^a-z0-9\u4e00-\u9fa5]', '', exp_str)
        act_clean = re.sub(r'[^a-z0-9\u4e00-\u9fa5]', '', act_str)
        
        return exp_clean == act_clean
