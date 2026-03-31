"""日志模块：使用 loguru 输出结构化日志到控制台和文件"""

import sys
from loguru import logger
from ai_sign.config import config

logger.remove()

logger.add(
    sys.stdout,
    level=config.log_level,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    colorize=True,
)

logger.add(
    "logs/ai_sign_{time:YYYY-MM-DD}.log",
    level="DEBUG",
    rotation="00:00",      # 每天零点滚动
    retention="30 days",   # 保留 30 天
    compression="zip",
    encoding="utf-8",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{line} - {message}",
)

__all__ = ["logger"]
