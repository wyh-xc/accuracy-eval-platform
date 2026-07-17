# 如何添加自定义评测策略

## 优化后的新增策略流程

现在你只需要 **1 个文件** 就可以添加新策略，无需修改任何现有代码！

### 步骤 1：创建策略文件

在 `strategies/plugins/` 目录下创建一个新文件，例如 `my_new_strategy.py`。

### 步骤 2：编写策略类

```python
"""
自定义策略示例：你的策略描述
"""

from ..base import EvaluationStrategy

class MyNewStrategy(EvaluationStrategy):
    """
    策略名称：你的策略显示名称
    逻辑：简要描述你的策略逻辑
    """
    
    # 定义策略 ID（在前端下拉框中使用的值）
    name = "my_new_strategy"
    
    def get_display_name(self):
        return "我的新策略"
    
    def evaluate(self, expected, actual):
        """
        实现你的评测逻辑
        
        参数:
            expected: 预期结果
            actual: 实际结果
            
        返回:
            bool: 评测是否通过
        """
        # 在这里写你的比较逻辑
        # 例如：
        if expected is None or actual is None:
            return False
        
        return str(expected) == str(actual)
```

### 步骤 3：重启服务或等待热加载

- **方式 A**：重启 Flask 应用，系统会自动扫描并加载新策略
- **方式 B**：调用 `StrategyRegistry.reload_plugins()` 方法热加载

就这么简单！系统会自动：
1. 扫描 `plugins` 目录
2. 发现所有继承 `EvaluationStrategy` 的类
3. 实例化并注册到策略列表中
4. 前端下拉框自动显示新策略

---

## 已内置的示例策略

项目中已经提供了两个示例插件：

### 1. 忽略标点符号策略 (`ignore_punctuation_strategy.py`)
- **ID**: `ignore_punctuation`
- **功能**: 去除所有标点符号和空格后进行比较
- **场景**: 适用于文本内容相同但标点格式不同的情况

### 2. 包含关系策略 (`contains_strategy.py`)
- **ID**: `contains`
- **功能**: 只要一方包含另一方即视为通过
- **场景**: 适用于接口返回内容较多，只需验证关键信息存在的场景

---

## 更多策略示例

### 示例 3：正则表达式匹配

```python
import re
from ..base import EvaluationStrategy

class RegexMatchStrategy(EvaluationStrategy):
    name = "regex_match"
    
    def get_display_name(self):
        return "正则表达式匹配"
    
    def evaluate(self, expected, actual):
        try:
            pattern = re.compile(str(expected))
            return bool(pattern.search(str(actual)))
        except:
            return False
```

### 示例 4：Levenshtein 距离（编辑距离）匹配

```python
from ..base import EvaluationStrategy

class EditDistanceStrategy(EvaluationStrategy):
    name = "edit_distance"
    
    def get_display_name(self):
        return "编辑距离匹配 (允许 2 个字符差异)"
    
    def evaluate(self, expected, actual):
        exp_str = str(expected)
        act_str = str(actual)
        
        # 简单的编辑距离计算
        if abs(len(exp_str) - len(act_str)) > 2:
            return False
        
        # 这里可以引入 python-Levenshtein 库进行精确计算
        # 简化版：只检查长度差异
        return abs(len(exp_str) - len(act_str)) <= 2
```

### 示例 5：JSON 字段匹配

```python
import json
from ..base import EvaluationStrategy

class JsonFieldStrategy(EvaluationStrategy):
    name = "json_field"
    
    def get_display_name(self):
        return "JSON 指定字段匹配"
    
    def evaluate(self, expected, actual):
        try:
            # expected 格式：{"field": "name", "value": "张三"}
            # actual 是 JSON 字符串
            config = json.loads(expected) if isinstance(expected, str) else expected
            data = json.loads(actual) if isinstance(actual, str) else actual
            
            field = config.get('field')
            expect_value = config.get('value')
            
            return data.get(field) == expect_value
        except:
            return False
```

---

## 高级用法

### 带参数的策略

```python
from ..base import EvaluationStrategy

class CustomThresholdStrategy(EvaluationStrategy):
    name = "custom_threshold"
    
    def __init__(self, threshold=0.9):
        self.threshold = threshold
    
    def get_display_name(self):
        return f"相似度匹配 (阈值：{self.threshold})"
    
    def evaluate(self, expected, actual):
        # 使用 self.threshold 进行判断
        similarity = self.calculate_similarity(expected, actual)
        return similarity >= self.threshold
    
    def calculate_similarity(self, a, b):
        # 实现相似度计算逻辑
        return 1.0 if a == b else 0.0
```

### 运行时动态注册

你也可以在代码中动态注册策略（无需创建文件）：

```python
from strategies.registry import StrategyRegistry

class MyDynamicStrategy(EvaluationStrategy):
    name = "dynamic_strategy"
    def evaluate(self, expected, actual):
        return True

# 注册
StrategyRegistry.register_custom_strategy("dynamic", MyDynamicStrategy)
```

---

## 故障排查

如果策略没有自动加载，请检查：

1. 文件是否在正确的目录：`strategies/plugins/`
2. 文件名是否以 `.py` 结尾且不以 `__` 开头
3. 类是否继承自 `EvaluationStrategy`
4. 是否定义了 `name` 属性
5. 查看控制台日志，是否有 `[错误]` 提示

可以通过以下代码查看所有可用策略：

```python
from strategies.registry import get_strategy_list
for s in get_strategy_list():
    print(f"{s['id']}: {s['name']}")
```
