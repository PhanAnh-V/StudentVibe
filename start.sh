
#!/bin/bash

# Start Flask web server with threading support
echo "Starting Flask web server with background processing..."
exec gunicorn --bind 0.0.0.0:5000 --reuse-port --reload --threads 4 main:app
