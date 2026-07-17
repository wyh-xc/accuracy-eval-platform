# AI 批阅项目评测工具使用说明

## 概述

本工具用于 AI 批改准确率的评测流程，包含两个步骤：

1. **批量提交任务**：读取 Excel/CSV 文件中的 `image_url` 列，批量提交到任务接口，获取 `taskid` 并保存到新文件
2. **获取任务结果并评测**：根据 `taskid` 获取任务结果，并使用自定义评测策略进行准确率评测

## 安装依赖

```bash
pip install -r requirements.txt
```

## 使用方法

### 步骤 1：批量提交任务

```bash
python batch_evaluator.py --step 1 \
    --input-file input.xlsx \
    --output-file tasks.xlsx \
    --api-url http://your-api.com/submit
```

**参数说明：**
- `--input-file`: 输入的 Excel/CSV 文件路径（必须包含 `image_url` 列）
- `--output-file`: 输出的 Excel 文件路径（将包含 `taskid` 列）
- `--api-url`: 任务提交接口 URL
- `--api-method`: HTTP 请求方法（默认：POST）
- `--api-input-field`: API 请求中输入字段的名称（默认：image_url）
- `--taskid-response-path`: 从 API 响应中提取 taskid 的路径（默认：taskid）
- `--delay`: 请求间隔时间（秒，默认：0.1）

**示例：**
```bash
# 基本用法
python batch_evaluator.py --step 1 -i input.xlsx -o tasks.xlsx --api-url http://api/submit

# 指定自定义响应路径
python batch_evaluator.py --step 1 -i input.xlsx -o tasks.xlsx --api-url http://api/submit --taskid-response-path data.task.id

# 添加请求头
python batch_evaluator.py --step 1 -i input.xlsx -o tasks.xlsx --api-url http://api/submit --api-headers '{"Authorization": "Bearer token"}'
```

### 步骤 2：获取任务结果并评测

```bash
python batch_evaluator.py --step 2 \
    --input-file tasks.xlsx \
    --result-file results.xlsx \
    --strategy exact_match \
    --expected-column expected
```

**参数说明：**
- `--input-file`: 包含 `taskid` 列的 Excel/CSV 文件路径
- `--result-file`: 输出结果文件路径
- `--taskid-column`: 包含 taskid 的列名（默认：taskid）
- `--result-api-url`: 查询任务结果的接口 URL（可选，如果文件已有实际结果则不需要）
- `--result-api-method`: 结果查询 HTTP 方法（默认：GET）
- `--result-response-path`: 从 API 响应中提取结果的路径（默认：result）
- `--status-response-path`: 从 API 响应中提取状态的路径（用于异步任务）
- `--max-retries`: 最大重试次数（默认：10）
- `--retry-delay`: 重试间隔时间（秒，默认：2.0）
- `--expected-column`: 包含预期结果的列名（默认：expected）
- `--strategy`: 评测策略 ID

**示例：**
```bash
# 从已有 actual 列读取结果并评测
python batch_evaluator.py --step 2 -i tasks.xlsx -r results.xlsx --strategy exact_match

# 通过 API 获取结果并评测
python batch_evaluator.py --step 2 -i tasks.xlsx -r results.xlsx --strategy exact_match --result-api-url http://api/result/{taskid}

# 使用忽略大小写策略
python batch_evaluator.py --step 2 -i tasks.xlsx -r results.xlsx --strategy case_insensitive
```

### 查看可用策略

```bash
python batch_evaluator.py --list-strategies
```

## 评测策略

系统支持插件式评测策略，将策略文件放在 `strategies/plugins/` 目录下即可自动加载。

### 内置策略

1. **exact_match**: 精确匹配（字符串完全相同）
2. **case_insensitive**: 忽略大小写匹配

### 自定义策略

创建自定义策略非常简单，只需在 `strategies/plugins/` 目录下创建一个 Python 文件：

```python
"""
自定义评测策略示例
"""
from strategies.base import EvaluationStrategy


class MyCustomStrategy(EvaluationStrategy):
    """自定义策略描述"""
    
    name = "my_custom"
    description = "我的自定义策略描述"
    
    def evaluate(self, expected, actual) -> bool:
        """
        评估实际值是否与预期值匹配
        
        参数:
            expected: 预期值
            actual: 实际值
            
        返回:
            bool: 匹配返回 True，否则返回 False
        """
        # 在这里实现你的比较逻辑
        return str(expected).strip() == str(actual).strip()
```

## 完整工作流程示例

### 场景 1：完整的 API 调用流程

```bash
# 1. 提交任务获取 taskid
python batch_evaluator.py --step 1 \
    --input-file images.xlsx \
    --output-file tasks.xlsx \
    --api-url http://api.com/submit

# 等待任务处理完成后...

# 2. 获取结果并评测
python batch_evaluator.py --step 2 \
    --input-file tasks.xlsx \
    --result-file results.xlsx \
    --result-api-url http://api.com/result/{taskid} \
    --strategy exact_match \
    --expected-column expected
```

### 场景 2：已有实际结果的评测

如果你的文件中已经包含了实际结果列（`actual`），可以直接评测：

```bash
python batch_evaluator.py --step 2 \
    --input-file data_with_actuals.xlsx \
    --result-file evaluation_results.xlsx \
    --strategy exact_match \
    --expected-column expected
```

## 输出文件格式

### 步骤 1 输出
包含原始数据的所有列，外加 `taskid` 列。

### 步骤 2 输出
包含所有输入列，外加：
- `actual_result`: 实际结果
- `error`: 错误信息（如果有）
- `match`: 是否匹配（True/False/None）

## 注意事项

1. **API 响应格式**：确保 API 返回的是 JSON 格式，且可以通过 `taskid_response_path` 或 `result_response_path` 提取所需字段
2. **异步任务**：对于异步任务，使用 `--status-response-path` 和 `--max-retries` 参数进行轮询
3. **文件编码**：CSV 文件支持多种编码（utf-8, gbk, gb2312, latin1），会自动尝试
4. **请求频率**：使用 `--delay` 参数控制请求频率，避免对 API 造成压力

## 故障排除

### 问题：策略未加载
- 检查策略文件是否在 `strategies/plugins/` 目录下
- 确保策略类继承自 `EvaluationStrategy`
- 确保策略类有 `name` 和 `evaluate()` 方法

### 问题：无法从 API 响应中提取数据
- 检查 `taskid_response_path` 或 `result_response_path` 是否正确
- 使用点号表示法访问嵌套字段，如 `data.result.value`

### 问题：任务一直处于 pending 状态
- 增加 `--max-retries` 参数
- 增加 `--retry-delay` 参数
- 检查 `--status-response-path` 是否正确
