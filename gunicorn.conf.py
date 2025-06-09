import multiprocessing
import os

# Server socket
bind = "0.0.0.0:" + str(os.getenv("PORT", "5000"))
backlog = 2048

# Worker processes
workers = 2  # Reduced number of workers
worker_class = "gevent"
worker_connections = 500  # Reduced connections
timeout = 60  # Increased timeout
keepalive = 2

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "debug"  # Changed to debug for more information

# Process naming
proc_name = "virtualtrade"

# Server mechanics
daemon = False
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None

# SSL
keyfile = None
certfile = None

# Server hooks
def on_starting(server):
    pass

def on_reload(server):
    pass

def on_exit(server):
    pass 