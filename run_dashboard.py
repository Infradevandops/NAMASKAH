#!/usr/bin/env python3
"""
Simple dashboard startup script
Handles database initialization and starts the server
"""

import os
import sys
import subprocess
from pathlib import Path

def check_requirements():
    """Check if required files exist"""
    required_files = [
        'main.py',
        'requirements.txt',
        '.env'
    ]
    
    missing = []
    for file in required_files:
        if not Path(file).exists():
            missing.append(file)
    
    if missing:
        print(f"❌ Missing required files: {', '.join(missing)}")
        if '.env' in missing:
            print("💡 Copy .env.example to .env and configure your API keys")
        return False
    
    return True

def install_dependencies():
    """Install Python dependencies"""
    print("📦 Installing dependencies...")
    try:
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'], 
                      check=True, capture_output=True)
        print("✅ Dependencies installed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def init_database():
    """Initialize database if needed"""
    if not Path('namaskah.db').exists():
        print("🗄️ Initializing database...")
        try:
            from main import Base, engine
            Base.metadata.create_all(bind=engine)
            print("✅ Database initialized")
        except Exception as e:
            print(f"❌ Database initialization failed: {e}")
            return False
    else:
        print("✅ Database exists")
    
    return True

def start_server():
    """Start the FastAPI server"""
    print("🚀 Starting Namaskah Dashboard...")
    print("📍 Dashboard: http://localhost:8000/app")
    print("🎛️ Admin Panel: http://localhost:8000/admin")
    print("📚 API Docs: http://localhost:8000/docs")
    print("=" * 50)
    
    try:
        subprocess.run([
            sys.executable, '-m', 'uvicorn', 
            'main:app', 
            '--reload', 
            '--host', '0.0.0.0', 
            '--port', '8000'
        ])
    except KeyboardInterrupt:
        print("\n👋 Dashboard stopped")
    except Exception as e:
        print(f"❌ Server error: {e}")

def main():
    print("🎯 Namaskah SMS Dashboard Startup")
    print("=" * 40)
    
    # Check requirements
    if not check_requirements():
        return 1
    
    # Install dependencies
    if not install_dependencies():
        return 1
    
    # Initialize database
    if not init_database():
        return 1
    
    # Start server
    start_server()
    return 0

if __name__ == "__main__":
    sys.exit(main())