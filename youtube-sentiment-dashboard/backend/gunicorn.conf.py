##############################################################
#  gunicorn.conf.py
#  Production Gunicorn configuration
#
#  Usage:
#    gunicorn -c gunicorn.conf.py wsgi:application
##############################################################

import multiprocessing

#   Workers                        ─
# Rule of thumb: 2–4 × CPU cores
workers     = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
threads     = 1

#   Binding                        ─
bind        = "0.0.0.0:5000"
backlog     = 2048

#   Timeouts                        
timeout          = 180   # Reddit comment fetching across posts can be slow
keepalive        = 5
graceful_timeout = 30

#   Logging                        ─
accesslog  = "-"          # stdout
errorlog   = "-"          # stderr
loglevel   = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)sµs'

#   Process naming                     
proc_name = "sentimentscope"

#   Preload app (shared memory for workers)        ─
preload_app = True

#   Security                        
limit_request_line   = 4096
limit_request_fields = 100

#   Hooks                         ─
def on_starting(server):
    server.log.info("SentimentScope API starting…")

def worker_exit(server, worker):
    server.log.info(f"Worker {worker.pid} exiting")
