import os
from app import app_instance

# Firebase App Hosting expects the WSGI app to be named 'app'
app = app_instance

if __name__ == '__main__':
    # Get port from environment or default to 8080 for Firebase App Hosting
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
