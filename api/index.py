# api/run.py
from monitor import run_monitor

def handler(request):
    """Vercel Serverless Function 入口"""
    result = run_monitor()
    return result
