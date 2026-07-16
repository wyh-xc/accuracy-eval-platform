"""
Flask application factory and configuration.
"""

import os
from flask import Flask, render_template, request, jsonify, send_from_directory
from werkzeug.exceptions import HTTPException

# Add parent directory to path for imports
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.file_handler import FileHandler
from core.api_client import APIClient
from core.evaluation_engine import EvaluationEngine
from strategies.registry import StrategyRegistry
from utils.helpers import save_uploaded_file, allowed_file


def create_app(config=None):
    """Application factory for creating Flask app."""
    
    app = Flask(__name__)
    
    # Default configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, '..', 'uploads')
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
    app.config['ALLOWED_EXTENSIONS'] = {'csv', 'xlsx', 'xls'}
    
    # Update config if provided
    if config:
        app.config.update(config)
    
    # Ensure upload folder exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Register routes
    register_routes(app)
    
    # Error handlers
    register_error_handlers(app)
    
    return app


def register_routes(app):
    """Register all application routes."""
    
    @app.route('/')
    def index():
        """Main page."""
        strategies = StrategyRegistry.get_strategy_list()
        return render_template('index.html', strategies=strategies)
    
    @app.route('/api/strategies', methods=['GET'])
    def get_strategies():
        """Get all available evaluation strategies."""
        strategies = StrategyRegistry.get_strategy_list()
        return jsonify({'success': True, 'strategies': strategies})
    
    @app.route('/api/file/columns', methods=['POST'])
    def get_file_columns():
        """Get columns from uploaded file."""
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename, app.config['ALLOWED_EXTENSIONS']):
            return jsonify({
                'success': False, 
                'error': f'File type not allowed. Allowed types: {", ".join(app.config["ALLOWED_EXTENSIONS"])}'
            }), 400
        
        # Save file temporarily
        filepath = save_uploaded_file(
            file, 
            app.config['UPLOAD_FOLDER'], 
            app.config['ALLOWED_EXTENSIONS']
        )
        
        if not filepath:
            return jsonify({'success': False, 'error': 'Failed to save file'}), 500
        
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
        """Run accuracy evaluation."""
        data = request.json
        
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        # Extract parameters
        filepath = data.get('filepath')
        input_column = data.get('input_column')
        expected_column = data.get('expected_column')
        actual_column = data.get('actual_column')
        strategy_id = data.get('strategy_id', 'exact_match')
        
        # API configuration (optional)
        api_url = data.get('api_url')
        api_method = data.get('api_method', 'POST')
        api_headers = data.get('api_headers', {})
        api_input_field = data.get('api_input_field', 'input')
        api_extract_path = data.get('api_extract_path')
        
        # Validate required fields
        if not filepath or not input_column or not expected_column:
            return jsonify({
                'success': False, 
                'error': 'Missing required parameters'
            }), 400
        
        # Get strategy
        strategy = StrategyRegistry.get_strategy(strategy_id)
        if not strategy:
            return jsonify({
                'success': False, 
                'error': f'Unknown strategy: {strategy_id}'
            }), 400
        
        # Create evaluation engine
        engine = EvaluationEngine(strategy)
        
        # Run evaluation
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
        """Create a custom evaluation strategy."""
        data = request.json
        
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        strategy_id = data.get('strategy_id')
        strategy_name = data.get('name')
        comparison_type = data.get('comparison_type', 'exact')
        tolerance = data.get('tolerance', 0.01)
        
        if not strategy_id or not strategy_name:
            return jsonify({
                'success': False, 
                'error': 'strategy_id and name are required'
            }), 400
        
        # Import here to avoid circular imports
        from strategies.base import EvaluationStrategy
        
        # Create dynamic strategy class based on type
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
                return f"Custom strategy: {self._comp_type}"
            
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
        
        # Register the custom strategy
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
                'message': f'Custom strategy "{strategy_name}" created successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to create custom strategy'
            }), 500
    
    @app.route('/uploads/<filename>')
    def uploaded_file(filename):
        """Serve uploaded files."""
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
    
    @app.route('/api/config', methods=['GET'])
    def get_config():
        """Get application configuration."""
        return jsonify({
            'allowed_extensions': list(app.config['ALLOWED_EXTENSIONS']),
            'max_file_size_mb': app.config['MAX_CONTENT_LENGTH'] // (1024 * 1024),
        })


def register_error_handlers(app):
    """Register error handlers."""
    
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
            'error': 'Internal server error',
            'message': str(e)
        }
        return jsonify(response), 500
