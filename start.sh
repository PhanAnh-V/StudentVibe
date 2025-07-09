
#!/bin/bash

# Start Flask web server
exec gunicorn --bind 0.0.0.0:5000 --reuse-port --reload main:app
