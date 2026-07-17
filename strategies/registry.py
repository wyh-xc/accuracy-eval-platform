"""
策略注册表模块，用于管理评测策略。
提供注册和检索策略的中心位置。
支持自动扫描 plugins 目录动态加载自定义策略。
"""

import os
import importlib
import inspect
from typing import Dict, List, Type, Optional
from .base import EvaluationStrategy


class StrategyRegistry:
    """用于管理评测策略的注册表（支持自动发现插件）。"""
    
    _instance = None
    _strategies: Dict[str, EvaluationStrategy] = {}
    _custom_strategies: Dict[str, Type[EvaluationStrategy]] = {}
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._initialize_builtin_strategies()
            self._load_plugin_strategies()
            self._initialized = True
    
    @classmethod
    def _initialize_builtin_strategies(cls):
        """初始化内置策略。"""
        try:
            from .builtin_strategies import (
                ExactMatchStrategy,
                CaseInsensitiveMatchStrategy,
                NumericToleranceStrategy,
                ContainsMatchStrategy,
                JSONMatchStrategy,
            )
            
            cls._strategies = {
                "exact_match": ExactMatchStrategy(),
                "case_insensitive": CaseInsensitiveMatchStrategy(),
                "numeric_tolerance": NumericToleranceStrategy(),
                "contains": ContainsMatchStrategy(),
                "json_match": JSONMatchStrategy(),
            }
        except ImportError as e:
            print(f"[警告] 加载内置策略失败：{e}")
            cls._strategies = {}
    
    @classmethod
    def _load_plugin_strategies(cls):
        """
        自动扫描 plugins 目录，动态加载所有自定义策略。
        无需修改任何代码，只需将策略文件放入 plugins 目录即可。
        """
        current_dir = os.path.dirname(__file__)
        plugins_dir = os.path.join(current_dir, 'plugins')
        
        if not os.path.exists(plugins_dir):
            print(f"[提示] 插件目录不存在：{plugins_dir}，将自动创建")
            os.makedirs(plugins_dir, exist_ok=True)
            # 创建 __init__.py
            init_file = os.path.join(plugins_dir, '__init__.py')
            if not os.path.exists(init_file):
                with open(init_file, 'w', encoding='utf-8') as f:
                    f.write("# 策略插件目录\n# 将自定义策略文件放在此目录下，系统会自动加载\n")
            return
        
        loaded_count = 0
        for filename in os.listdir(plugins_dir):
            if filename.endswith('.py') and not filename.startswith('__'):
                module_name = filename[:-3]  # 去掉 .py
                try:
                    # 动态导入模块
                    module = importlib.import_module(f'.plugins.{module_name}', package='strategies')
                    
                    # 遍历模块中找到所有继承自 EvaluationStrategy 的类
                    for name, obj in inspect.getmembers(module):
                        if (inspect.isclass(obj) and 
                            issubclass(obj, EvaluationStrategy) and 
                            obj is not EvaluationStrategy):
                            
                            instance = obj()
                            # 优先使用实例的 name 属性，否则使用类名转换
                            strategy_id = getattr(instance, 'name', name.replace('Strategy', '').lower())
                            
                            if strategy_id in cls._strategies:
                                print(f"[警告] 策略 '{strategy_id}' 重复，插件版本将覆盖内置版本 (来自 {filename})")
                            
                            cls._strategies[strategy_id] = instance
                            cls._custom_strategies[strategy_id] = obj
                            print(f"[插件] 已加载策略：{strategy_id} (来自 {filename})")
                            loaded_count += 1
                    
                except Exception as e:
                    print(f"[错误] 加载策略文件 {filename} 失败：{str(e)}")
        
        if loaded_count > 0:
            print(f"[系统] 共加载 {loaded_count} 个插件策略")
    
    @classmethod
    def reload_plugins(cls):
        """重新加载插件策略（支持热更新）。"""
        cls._custom_strategies.clear()
        # 保留内置策略
        builtin_ids = list(cls._strategies.keys())
        cls._initialize_builtin_strategies()
        # 重新加载插件
        cls._load_plugin_strategies()
        print("[系统] 插件策略已重新加载")
    
    @classmethod
    def get_strategy(cls, strategy_id: str) -> Optional[EvaluationStrategy]:
        """根据 ID 获取策略。"""
        return cls._strategies.get(strategy_id)
    
    @classmethod
    def get_all_strategies(cls) -> Dict[str, EvaluationStrategy]:
        """获取所有已注册的策略。"""
        return cls._strategies.copy()
    
    @classmethod
    def get_strategy_list(cls) -> List[Dict[str, str]]:
        """获取策略名称和描述列表。"""
        result = []
        for strategy_id, strategy in cls._strategies.items():
            result.append({
                "id": strategy_id,
                "name": strategy.name,
                "description": strategy.description,
                "is_custom": strategy_id in cls._custom_strategies
            })
        return result
    
    @classmethod
    def register_custom_strategy(
        cls, 
        strategy_id: str, 
        strategy_class: Type[EvaluationStrategy],
        **kwargs
    ) -> bool:
        """
        手动注册自定义策略（运行时动态添加）。
        
        参数:
            strategy_id: 策略的唯一标识符
            strategy_class: 要注册的策略类
            **kwargs: 传递给策略构造函数的额外参数
            
        返回:
            bool: 注册成功返回 True，否则返回 False
        """
        try:
            instance = strategy_class(**kwargs) if kwargs else strategy_class()
            cls._strategies[strategy_id] = instance
            cls._custom_strategies[strategy_id] = strategy_class
            return True
        except Exception as e:
            print(f"注册自定义策略失败：{e}")
            return False
    
    @classmethod
    def unregister_custom_strategy(cls, strategy_id: str) -> bool:
        """
        注销自定义策略。
        
        参数:
            strategy_id: 要移除的策略 ID
            
        返回:
            bool: 注销成功返回 True，否则返回 False
        """
        if strategy_id in cls._custom_strategies:
            del cls._strategies[strategy_id]
            del cls._custom_strategies[strategy_id]
            return True
        return False
    
    @classmethod
    def is_custom_strategy(cls, strategy_id: str) -> bool:
        """检查策略是否为自定义策略。"""
        return strategy_id in cls._custom_strategies


# 便捷函数（保持向后兼容）
def get_strategy_registry():
    """获取策略注册表单例。"""
    return StrategyRegistry()


def get_strategy(strategy_id: str):
    """获取策略实例。"""
    registry = get_strategy_registry()
    return registry.get_strategy(strategy_id)


def get_strategy_list():
    """获取策略列表。"""
    registry = get_strategy_registry()
    return registry.get_strategy_list()
