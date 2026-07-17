#!/usr/bin/env python3
"""
准确率评测系统的主入口点。
"""

import os
import sys

# 将父目录添加到路径以便导入
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app


def main():
    """运行应用程序。"""
    app = create_app()
    
    # 从环境变量获取配置
    host = os.environ.get('HOST', '0.0.0.0')
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('DEBUG', 'true').lower() == 'true'
    
    print(f"🚀 启动准确率评测系统")
    print(f"📍 运行于 http://{host}:{port}")
    print(f"🔧 调试模式：{debug}")
    print("\n按 CTRL+C 退出\n")
    
    app.run(host=host, port=port, debug=debug)


if __name__ == '__main__':
    main()
