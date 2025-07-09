
#!/usr/bin/env python3
import os
import subprocess
import threading
import time
import logging

logging.basicConfig(level=logging.INFO)

def run_web_server():
    """Run the Flask web application"""
    logging.info("Starting Flask web server...")
    subprocess.run([
        "gunicorn", 
        "--bind", "0.0.0.0:5000", 
        "--reuse-port", 
        "--reload", 
        "main:app"
    ])

def run_worker():
    """Run the Redis worker"""
    logging.info("Starting Redis worker...")
    from rq import Worker, Queue, Connection
    from redis import Redis
    import os
    
    # Wait a bit for Redis to be ready
    time.sleep(5)
    
    try:
        redis_url = os.getenv("REDIS_URL")
        if redis_url:
            redis_conn = Redis.from_url(redis_url)
        else:
            redis_conn = Redis(host='localhost', port=6379, db=0)
        
        with Connection(redis_conn):
            worker = Worker(map(Queue, ['default']))
            worker.work()
    except Exception as e:
        logging.error(f"Worker failed to start: {e}")

if __name__ == "__main__":
    # Start worker in background thread
    worker_thread = threading.Thread(target=run_worker, daemon=True)
    worker_thread.start()
    
    # Start web server in main thread
    run_web_server()
