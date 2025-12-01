"""
Gunicorn configuration file for production deployment.
This file configures Gunicorn to run the Django application with optimal settings.

Usage:
    gunicorn -c gunicorn_config.py backend.asgi:application
"""

import multiprocessing
import os

# Server socket
bind = os.getenv('GUNICORN_BIND', '0.0.0.0:8000')
backlog = 2048

# Worker processes
workers = int(os.getenv('GUNICORN_WORKERS', multiprocessing.cpu_count() * 2 + 1))
worker_class = 'uvicorn.workers.UvicornWorker'  # ASGI worker for Channels support
worker_connections = 1000
threads = int(os.getenv('GUNICORN_THREADS', 2))
max_requests = 1000  # Restart workers after this many requests (prevents memory leaks)
max_requests_jitter = 100  # Add jitter to prevent all workers restarting at once
timeout = int(os.getenv('GUNICORN_TIMEOUT', 600))  # Worker timeout in seconds (10 minutes for large file uploads)
graceful_timeout = 30  # Time to wait for workers to finish before killing them
keepalive = 5  # Seconds to wait for requests on a Keep-Alive connection

# Process naming
proc_name = 'deenbridge_backend'

# Server mechanics
daemon = False  # Don't run in background (let systemd/docker handle this)
pidfile = None  # Don't create a PID file
umask = 0o007
user = None  # Run as current user (set via systemd/docker)
group = None  # Run as current group
tmp_upload_dir = None

# Logging
accesslog = '-'  # Log to stdout
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'
errorlog = '-'  # Log to stderr
loglevel = os.getenv('GUNICORN_LOG_LEVEL', 'info')
capture_output = True  # Redirect stdout/stderr to error log
enable_stdio_inheritance = True

# Security
limit_request_line = 4096
limit_request_fields = 100
limit_request_field_size = 8190

# Server hooks
def on_starting(server):
    """
    Called just before the master process is initialized.
    """
    print("=" * 80)
    print("Starting Deen Bridge Backend Server")
    print("=" * 80)
    print(f"Workers: {workers}")
    print(f"Worker class: {worker_class}")
    print(f"Threads per worker: {threads}")
    print(f"Bind: {bind}")
    print(f"Timeout: {timeout}s")
    print("=" * 80)


def on_reload(server):
    """
    Called to recycle workers during a reload via SIGHUP.
    """
    print("Reloading workers...")


def when_ready(server):
    """
    Called just after the server is started.
    """
    print("Server is ready. Accepting connections.")


def pre_fork(server, worker):
    """
    Called just before a worker is forked.
    """
    pass


def post_fork(server, worker):
    """
    Called just after a worker has been forked.
    """
    pass


def pre_exec(server):
    """
    Called just before a new master process is forked.
    """
    pass


def worker_int(worker):
    """
    Called when a worker receives the SIGINT or SIGQUIT signal.
    """
    pass


def worker_abort(worker):
    """
    Called when a worker times out.
    """
    pass


def post_worker_init(worker):
    """
    Called just after a worker has initialized the application.
    """
    pass


def worker_exit(server, worker):
    """
    Called just after a worker has been exited.
    """
    pass


def child_exit(server, worker):
    """
    Called just after a worker has been exited, in the master process.
    """
    pass


def nworkers_changed(server, new_value, old_value):
    """
    Called just after num_workers has been changed.
    """
    print(f"Number of workers changed from {old_value} to {new_value}")


def on_exit(server):
    """
    Called just before exiting Gunicorn.
    """
    print("Shutting down Deen Bridge Backend Server")

