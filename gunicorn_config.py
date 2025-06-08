import multiprocessing
import os

# Server socket
bind = "0.0.0.0:" + str(os.getenv("PORT", "5000"))
backlog = 2048

# Worker processes
workers = 2
worker_class = 'sync'
worker_connections = 1000
timeout = 30
keepalive = 2

# Logging
accesslog = "-"  # Log to stdout
errorlog = "-"   # Log to stderr
loglevel = "debug"
capture_output = True
enable_stdio_inheritance = True

# Process naming
proc_name = 'gunicorn_vta'

# SSL
keyfile = None
certfile = None

# Server mechanics
daemon = False
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None 