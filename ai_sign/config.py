"""配置管理模块：从 .env 文件或环境变量加载所有运行时参数"""

import os
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    # 账号
    mobile: str = field(default_factory=lambda: os.getenv("DINGTALK_MOBILE", ""))
    password: str = field(default_factory=lambda: os.getenv("DINGTALK_PASSWORD", ""))

    # 定时 cron 表达式
    checkin_cron: str = field(default_factory=lambda: os.getenv("CHECKIN_CRON", "0 9 * * 1-5"))
    checkout_cron: str = field(default_factory=lambda: os.getenv("CHECKOUT_CRON", "0 18 * * 1-5"))

    # GPS 位置
    latitude: float = field(default_factory=lambda: float(os.getenv("LOCATION_LATITUDE", "39.9042")))
    longitude: float = field(default_factory=lambda: float(os.getenv("LOCATION_LONGITUDE", "116.4074")))
    address: str = field(default_factory=lambda: os.getenv("LOCATION_ADDRESS", ""))

    # 随机延迟（秒）
    delay_min: int = field(default_factory=lambda: int(os.getenv("RANDOM_DELAY_MIN", "0")))
    delay_max: int = field(default_factory=lambda: int(os.getenv("RANDOM_DELAY_MAX", "300")))

    # Server 酱通知
    serverchan_key: str = field(default_factory=lambda: os.getenv("SERVERCHAN_KEY", ""))

    # 日志
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))

    def validate(self) -> None:
        """校验必填配置项"""
        if not self.mobile:
            raise ValueError("DINGTALK_MOBILE 未配置，请在 .env 文件中设置手机号")
        if not self.password:
            raise ValueError("DINGTALK_PASSWORD 未配置，请在 .env 文件中设置密码")


# 全局单例
config = Config()
