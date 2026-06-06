import time

time_a = time.time()
import click
import sys
import uvicorn
from uvicorn.lifespan.on import LifespanOn

# from tools.locate_print import locate_print
# locate_print("'udadmin:User'")

# 你原来的自定义日志（保留，这是唯一在旧版 uvicorn 能跑的）
class UdLifespanOn(LifespanOn):
    async def startup(self) -> None:
        await super().startup()

        addr = click.style(
            f"http://{self.config.host}:{self.config.port}",
            bold=True, fg=(97, 175, 254),
        )
        self.logger.info(f"Server running on {addr} (Press CTRL+C to quit)")
        spend = click.style(f"{time.time() - time_a:.6f}", bold=True, fg=(255, 0, 255))
        self.logger.info(f"sever startup in {spend} seconds.")

sys.modules["uvicorn.lifespan.on"].LifespanOn = UdLifespanOn # type: ignore

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="localhost",
        port=3014,
        reload=True,
    )