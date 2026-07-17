"""
Flask 应用工厂和配置。
"""

import os
from flask import Flask, render_template, request, jsonify, send_from_directory
from werkzeug.exceptions import HTTPException

# 将父目录添加到路径以便导入
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.file_handler import FileHandler
from core.api_client import APIClient
from core.evaluation_engine import EvaluationEngine
from strategies.registry import StrategyRegistry
from utils.helpers import save_uploaded_file, allowed_file


def create_app(config=None):
    """创建 Flask 应用的应用工厂函数。"""
    
    app = Flask(__name__)
    
    # 默认配置
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, '..', 'uploads')
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 最大文件大小 16MB
    app.config['ALLOWED_EXTENSIONS'] = {'csv', 'xlsx', 'xls'}
    
    # 如果提供了配置则更新
    if config:
        app.config.update(config)
    
    # 确保上传文件夹存在
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # 注册路由
    register_routes(app)
    
    # 注册错误处理器
    register_error_handlers(app)
    
    return app


def register_routes(app):
    """注册所有应用程序路由。"""
    
    @app.route('/')
    def index():
        """主页面。"""
        strategies = StrategyRegistry.get_strategy_list()
        return render_template('index.html', strategies=strategies)
    
    @app.route('/api/strategies', methods=['GET'])
    def get_strategies():
        """获取所有可用的评测策略。"""
        strategies = StrategyRegistry.get_strategy_list()
        return jsonify({'success': True, 'strategies': strategies})
    
    @app.route('/api/file/columns', methods=['POST'])
    def get_file_columns():
        """从上传的文件中获取列信息。"""
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': '没有上传文件'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'success': False, 'error': '未选择文件'}), 400
        
        if not allowed_file(file.filename, app.config['ALLOWED_EXTENSIONS']):
            return jsonify({
                'success': False, 
                'error': f'不允许的文件类型。允许的类型：{", ".join(app.config["ALLOWED_EXTENSIONS"])}'
            }), 400
        
        # 临时保存文件
        filepath = save_uploaded_file(
            file, 
            app.config['UPLOAD_FOLDER'], 
            app.config['ALLOWED_EXTENSIONS']
        )
        
        if not filepath:
            return jsonify({'success': False, 'error': '保存文件失败'}), 500
        
        try:
            columns = FileHandler.get_columns(filepath)
            return jsonify({
                'success': True, 
                'columns': columns,
                'filepath': filepath
            })
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/evaluate', methods=['POST'])
    def evaluate():
        """运行准确率评测。"""
        data = request.json
        
        if not data:
            return jsonify({'success': False, 'error': '未提供数据'}), 400
        
        # 提取参数
        filepath = data.get('filepath')
        input_column = data.get('input_column')
        expected_column = data.get('expected_column')
        actual_column = data.get('actual_column')
        strategy_id = data.get('strategy_id', 'exact_match')
        
        # API 配置（可选）
        api_url = data.get('api_url')
        api_method = data.get('api_method', 'POST')
        api_headers = data.get('api_headers', {})
        api_input_field = data.get('api_input_field', 'input')
        api_extract_path = data.get('api_extract_path')
        
        # 验证必填字段
        if not filepath or not input_column or not expected_column:
            return jsonify({
                'success': False, 
                'error': '缺少必填参数'
            }), 400
        
        # 获取策略
        strategy = StrategyRegistry.get_strategy(strategy_id)
        if not strategy:
            return jsonify({
                'success': False, 
                'error': f'未知策略：{strategy_id}'
            }), 400
        
        # 创建评测引擎
        engine = EvaluationEngine(strategy)
        
        # 运行评测
        result = engine.evaluate_from_file(
            file_path=filepath,
            input_column=input_column,
            expected_column=expected_column,
            actual_column=actual_column,
            api_url=api_url,
            api_method=api_method,
            api_headers=api_headers,
            api_input_field=api_input_field,
            api_extract_path=api_extract_path,
        )
        
        return jsonify({
            'success': True,
            'result': result.to_dict()
        })
    
    @app.route('/api/strategies/custom', methods=['POST'])
    def create_custom_strategy():
        """创建自定义评测策略。"""
        data = request.json
        
        if not data:
            return jsonify({'success': False, 'error': '未提供数据'}), 400
        
        strategy_id = data.get('strategy_id')
        strategy_name = data.get('name')
        comparison_type = data.get('comparison_type', 'exact')
        tolerance = data.get('tolerance', 0.01)
        
        if not strategy_id or not strategy_name:
            return jsonify({
                'success': False, 
                'error': 'strategy_id 和 name 是必填项'
            }), 400
        
        # 在此处导入以避免循环导入
        from strategies.base import EvaluationStrategy
        
        # 根据类型创建动态策略类
        class DynamicStrategy(EvaluationStrategy):
            def __init__(self, name, comp_type='exact', tol=0.01):
                self._name = name
                self._comp_type = comp_type
                self._tolerance = tol
            
            @property
            def name(self):
                return self._name
            
            @property
            def description(self):
                return f"自定义策略：{self._comp_type}"
            
            def evaluate(self, expected, actual):
                if self._comp_type == 'exact':
                    return str(expected).strip() == str(actual).strip()
                elif self._comp_type == 'case_insensitive':
                    return str(expected).strip().lower() == str(actual).strip().lower()
                elif self._comp_type == 'contains':
                    return str(expected).strip() in str(actual).strip()
                elif self._comp_type == 'numeric':
                    try:
                        return abs(float(expected) - float(actual)) <= self._tolerance
                    except (ValueError, TypeError):
                        return False
                else:
                    return str(expected).strip() == str(actual).strip()
        
        # 注册自定义策略
        success = StrategyRegistry.register_custom_strategy(
            strategy_id=strategy_id,
            strategy_class=DynamicStrategy,
            name=strategy_name,
            comp_type=comparison_type,
            tol=tolerance,
        )
        
        if success:
            return jsonify({
                'success': True,
                'message': f'自定义策略"{strategy_name}"创建成功'
            })
        else:
            return jsonify({
                'success': False,
                'error': '创建自定义策略失败'
            }), 500
    
    @app.route('/uploads/<filename>')
    def uploaded_file(filename):
        """提供上传的文件。"""
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
    
    @app.route('/api/config', methods=['GET'])
    def get_config():
        """获取应用程序配置。"""
        return jsonify({
            'allowed_extensions': list(app.config['ALLOWED_EXTENSIONS']),
            'max_file_size_mb': app.config['MAX_CONTENT_LENGTH'] // (1024 * 1024),
        })


def register_error_handlers(app):
    """注册错误处理器。"""
    
    @app.errorhandler(HTTPException)
    def handle_http_exception(e):
        response = {
            'success': False,
            'error': e.description,
            'code': e.code
        }
        return jsonify(response), e.code
    
    @app.errorhandler(Exception)
    def handle_exception(e):
        response = {
            'success': False,
            'error': '内部服务器错误',
            'message': str(e)
        }
        return jsonify(response), 500
