```python

# 这个全局错误处理无效
@app.exception_handler(Exception)
def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"message": str(exc)},
    )


# 全局错误处理，父app会覆盖子app的处理
@app.middleware("http")
async def global_exception_handler(request: Request, call_next):
    try:
        response = await call_next(request)
    except Exception as e:
        trace = traceback.format_exc()
        # 处理异常
        content = {
            "status": 5000,
            "error": str(e),
            "trace": str(trace),
        }
        return JSONResponse(status_code=500, content=content)
    return response



```