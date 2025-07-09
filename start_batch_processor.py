#!/usr/bin/env python3
"""
Start the batch processor as a background service
"""

import subprocess
import sys
import os
import time
import signal

def start_batch_processor():
    """Start the batch processor in a loop"""
    print("Starting batch processor service...")
    
    while True:
        try:
            # Run the batch processor
            print("Running batch processor...")
            result = subprocess.run([sys.executable, "batch_processor.py"], 
                                  capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                print("Batch processor completed successfully")
                print(result.stdout)
            else:
                print(f"Batch processor failed with return code {result.returncode}")
                print(result.stderr)
            
            # Wait 30 seconds before running again
            print("Waiting 30 seconds before next run...")
            time.sleep(30)
            
        except subprocess.TimeoutExpired:
            print("Batch processor timed out, restarting...")
            continue
        except KeyboardInterrupt:
            print("Batch processor service stopped")
            break
        except Exception as e:
            print(f"Error in batch processor service: {e}")
            time.sleep(10)  # Wait before retrying

if __name__ == "__main__":
    start_batch_processor()