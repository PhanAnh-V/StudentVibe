#!/usr/bin/env python3
"""
Clean test server that loads environment variables safely
Use this for testing without exposing secrets
"""
import os
from pathlib import Path

def load_env_safely():
    """Load environment variables from .env file or use defaults"""
    env_file = Path('.env')
    
    if env_file.exists():
        # Load from .env file if it exists
        with open(env_file) as f:
            for line in f:
                if line.strip() and not line.startswith('#') and '=' in line:
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value
        print("✅ Loaded environment variables from .env file")
    else:
        # Use safe defaults for testing
        defaults = {
            'SECRET_KEY': 'dev-secret-key-for-flask-sessions',
            'OPENAI_API_KEY': 'test-key-placeholder',
            'FIREBASE_API_KEY': 'test-firebase-key-placeholder'
        }
        
        for key, value in defaults.items():
            if key not in os.environ:
                os.environ[key] = value
        
        print("⚠️  Using default test values. Create .env file for real keys.")

if __name__ == "__main__":
    # Load environment variables safely
    load_env_safely()
    
    # Import the app after setting environment variables
    from app import create_app
    
    # Create and run the app
    app = create_app()
    print("\n🚀 Starting VibeCheck test server...")
    print("📍 Server will be available at: http://localhost:5001")
    print("🔧 Environment: Test/Development")
    print("⚡ Ready for testing!\n")
    
    app.run(host='0.0.0.0', port=5001, debug=True)
