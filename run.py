#!/usr/bin/env python3
"""
失物招領系統啟動文件
Run the application with: python run.py
"""

import os
from app import create_app

if __name__ == '__main__':
    app = create_app()
    
    # Configuration for development
    debug_mode = os.environ.get('FLASK_ENV', 'development') == 'development'
    port = int(os.environ.get('PORT', 5000))
    
    print(f"\n{'='*50}")
    print("🎓 學校失物招領系統")
    print(f"{'='*50}")
    print(f"✅ 應用已啟動")
    print(f"🌐 訪問地址: http://localhost:{port}")
    print(f"📝 調試模式: {'開啟' if debug_mode else '關閉'}")
    print(f"{'='*50}\n")
    
    app.run(debug=debug_mode, host='0.0.0.0', port=port)
