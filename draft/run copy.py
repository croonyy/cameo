import time
time_a = time.time()
import uvicorn
from uvicorn.lifespan.on import LifespanOn
import click
import sys

# import subprocess
# import os
import multiprocessing

# from tools.locate_print import locate_print
# locate_print("'udadmin:User'")


class UdLifespanOn(LifespanOn):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    async def startup(self) -> None:
        await super().startup()

        # ud add
        addr = click.style(
            f"http://{self.config.host}:{self.config.port}",
            bold=True,
            # fg=(255, 12, 128),
            fg=(97, 175, 254),
        )
        self.logger.info(f"Server running on {addr} (Press CTRL+C to quit)")
        time_b = time.time()
        spend = click.style(f"{time_b - time_a:.6f}", bold=True, fg=(255, 0, 255))
        self.logger.info(f"sever startup in {spend} seconds.")


sys.modules["uvicorn.lifespan.on"].LifespanOn = UdLifespanOn # type: ignore


def run_server():
    uvicorn.run("main:app", host="localhost", port=3014, reload=True)

# 启动应用
if __name__ == "__main__":
    # uvicorn.run("main:app", host="localhost", port=3014, reload=True) # ctrl+c 终止的时候  reloader有时候异常导致不能正常退出，导致服务不能终止
    # 使用子进程来启动服务
    server_process = multiprocessing.Process(target=run_server) # 创建子进程绑定uvicorn服务入口
    server_process.start() # 启动子进程
    print(f"server PID: {server_process.pid}") # 可读取子进程的pid，可用于后续根据进程id做某些操作
    
    try:
        server_process.join()  # 阻塞主线程，直到子进程结束
    except KeyboardInterrupt:
        print("terminate server...")
        server_process.terminate()  # 发送子进程 SIGTERM(终止信号)
        server_process.join(timeout=0.5)
        print(f"server_process.is_alive():{server_process.is_alive()}")
        if server_process.is_alive():
            print("Force killing server...")
            server_process.kill() # 如果子进程在5秒内没有终止，则发送 SIGKILL(强制终止信号)
        print("terminate success")

    
