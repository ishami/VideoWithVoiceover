import os
import env_init  # Force load env vars

bind = "0.0.0.0:8000"
workers = 4
timeout = 300
preload_app = True  # This loads the app before forking workers

def when_ready(server):
    """Called just after the server is started."""
    print(f"[gunicorn] Server ready with API keys loaded")
    print(f"[gunicorn] PIXABAY_API_KEY: {os.getenv('PIXABAY_API_KEY', 'NOT SET')[:8]}...")

def worker_init(worker):
    """Called just after a worker has been forked."""
    print(f"[gunicorn] Worker {worker.pid} initialized with API keys")
