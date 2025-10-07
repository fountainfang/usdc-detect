from monitor import run_monitor

def handler(request):
    """Vercel Serverless Function 入口"""
    try:
        result = run_monitor()
        # 返回 JSON 响应
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": result
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": {"error": str(e)}
        }
