#!/usr/bin/env python3
"""
Main entry point for the Accuracy Evaluation System.
"""

import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app


def main():
    """Run the application."""
    app = create_app()
    
    # Get configuration from environment
    host = os.environ.get('HOST', '0.0.0.0')
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('DEBUG', 'true').lower() == 'true'
    
    print(f"🚀 Starting Accuracy Evaluation System")
    print(f"📍 Running on http://{host}:{port}")
    print(f"🔧 Debug mode: {debug}")
    print("\nPress CTRL+C to quit\n")
    
    app.run(host=host, port=port, debug=debug)


if __name__ == '__main__':
    main()
