
#!/bin/bash

# Start Flask web server with threading support
echo "Starting Flask web server with background processing..."
exec gunicorn --bind 0.0.0.0:5000 --reuse-port --reload --worker-class gthread --threads 4 --worker-connections 1000 main:app
