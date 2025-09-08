#!/usr/bin/env python3
"""
Simple server startup script
"""
import uvicorn
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    try:
        print("Starting CumApp server...")
        
        # Import the app
        from main import app
        print("App imported successfully")
        
        # Start the server
        uvicorn.run(
            app, 
            host="0.0.0.0", 
            port=8001, 
            log_level="info",
            reload=False
        )
        
    except Exception as e:
        print(f"Error starting server: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    main()