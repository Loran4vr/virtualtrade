import multiprocessing
import os

# Server socket
bind = "0.0.0.0:" + str(os.getenv("PORT", "5000"))
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "gevent"
worker_connections = 1000
timeout = 30
keepalive = 2

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"

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