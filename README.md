# Accuracy Evaluation System

准确率评测系统 - 一个用于评估 API 响应准确率的 Web 应用。

## 功能特性

1. **文件上传**: 支持 Excel (.xlsx, .xls) 和 CSV 文件格式
2. **自定义接口**: 用户可以配置要访问的 API 接口
3. **列选择**: 自由选择输入数据列、预期结果列、实际结果列
4. **多种评测策略**: 
   - 精确匹配
   - 忽略大小写匹配
   - 数值容差匹配
   - 包含匹配
   - JSON 结构匹配
5. **自定义策略**: 用户可以创建自己的评测逻辑
6. **可视化结果**: 清晰展示评测统计和详细结果

## 项目结构

```
/workspace
├── app/                    # Flask 应用
│   └── __init__.py        # 应用工厂和路由
├── core/                   # 核心业务逻辑
│   ├── __init__.py
│   ├── file_handler.py    # 文件处理模块
│   ├── api_client.py      # API 客户端
│   └── evaluation_engine.py # 评测引擎
├── strategies/             # 评测策略
│   ├── __init__.py
│   ├── base.py            # 策略基类
│   ├── builtin_strategies.py # 内置策略
│   └── registry.py        # 策略注册表
├── utils/                  # 工具函数
│   ├── __init__.py
│   └── helpers.py         # 辅助函数
├── templates/              # HTML 模板
│   └── index.html         # 主页面
├── static/                 # 静态资源
├── uploads/                # 上传文件目录 (运行时创建)
├── run.py                  # 启动脚本
├── requirements.txt        # 依赖列表
└── README.md              # 说明文档
```

## 安装

```bash
pip install -r requirements.txt
```

## 运行

```bash
python run.py
```

或者使用环境变量配置：

```bash
HOST=0.0.0.0 PORT=5000 DEBUG=true python run.py
```

## 使用说明

### 1. 上传文件
- 点击或拖拽上传 Excel/CSV 文件
- 系统会自动解析文件并显示可用列

### 2. 选择数据列
- **输入数据列**: 包含发送给 API 的输入数据
- **预期结果列**: 包含期望的正确结果
- **实际结果列** (可选): 如果文件中已有实际结果，可选择此项；否则通过 API 获取

### 3. 配置 API (可选)
- 启用 API 调用以获取实际结果
- 配置 API URL、请求方法、请求头等
- 设置响应提取路径（如 `result.data`）

### 4. 选择评测策略
- 从下拉列表选择合适的评测逻辑
- 或创建自定义策略

### 5. 开始评测
- 点击"开始评测"按钮
- 查看评测结果统计和详细对比

## 自定义策略

可以通过界面创建自定义策略，支持以下比较类型：
- **精确匹配**: 字符串完全相同
- **忽略大小写**: 比较时忽略大小写
- **包含匹配**: 实际值包含预期值
- **数值容差**: 允许数值在一定误差范围内

## API 端点

- `GET /`: 主页面
- `GET /api/strategies`: 获取所有评测策略
- `POST /api/file/columns`: 上传文件并获取列信息
- `POST /api/evaluate`: 执行评测
- `POST /api/strategies/custom`: 创建自定义策略
- `GET /api/config`: 获取应用配置

## 架构设计

本系统采用以下设计模式：

1. **策略模式 (Strategy Pattern)**: 评测逻辑可插拔，易于扩展
2. **工厂模式 (Factory Pattern)**: 应用工厂创建 Flask 实例
3. **单一职责原则**: 各模块职责清晰，低耦合高复用

## 技术栈

- **后端**: Python, Flask
- **数据处理**: Pandas
- **HTTP 客户端**: Requests
- **前端**: HTML5, CSS3, JavaScript (原生)

## License

MIT License
