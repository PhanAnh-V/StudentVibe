
#!/bin/bash

# Start Redis worker in background
echo "Starting Redis worker..."
python -c "
from rq import Worker, Queue, Connection
from redis import Redis
import os
import time

time.sleep(5)  # Wait for Redis to be ready

try:
    redis_url = os.getenv('REDIS_URL')
    if redis_url:
        redis_conn = Redis.from_url(redis_url)
    else:
        redis_conn = Redis(host='localhost', port=6379, db=0)
    
    with Connection(redis_conn):
        worker = Worker(map(Queue, ['default']))
        worker.work()
except Exception as e:
    print(f'Worker failed: {e}')
" &

# Start Flask web server
echo "Starting Flask web server..."
exec gunicorn --bind 0.0.0.0:5000 --reuse-port --reload main:app
