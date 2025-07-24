"""
WSGI entry point for Firebase App Hosting
"""
import os
from app import app_instance as application

# Firebase App Hosting expects the WSGI application to be named 'application'
app = application

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 8080))
    application.run(host='0.0.0.0', port=port, debug=False)
