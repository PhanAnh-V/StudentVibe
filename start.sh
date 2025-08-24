
#!/bin/bash

# Start script for Firebase App Hosting
echo "Starting VibeCheck Flask application..."

# Set environment variables
export FLASK_ENV=production
export PYTHONPATH=/workspace

# Start the application using gunicorn
exec gunicorn --bind 0.0.0.0:${PORT:-8080} --workers 1 --timeout 120 wsgi:application
