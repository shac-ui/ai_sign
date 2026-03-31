"""配置管理模块：从 .env 文件或环境变量加载所有运行时参数"""

import os
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    # 钉钉 Web Cookie（从浏览器开发者工具中抓取）
    # 必填：dingtalk_token（也叫 dtoken），登录后有效期约 7 天
    dingtalk_token: str = field(default_factory=lambda: os.getenv("DINGTALK_TOKEN", ""))
    # 必填：登录用户的 userId（员工 ID），在 Cookie 或接口响应中可找到
    dingtalk_user_id: str = field(default_factory=lambda: os.getenv("DINGTALK_USER_ID", ""))
    # 可选：完整 Cookie 字符串，部分接口需要额外 Cookie 字段时使用
    dingtalk_cookie: str = field(default_factory=lambda: os.getenv("DINGTALK_COOKIE", ""))

    # 定时 cron 表达式（分 时 日 月 周）
    checkin_cron: str = field(default_factory=lambda: os.getenv("CHECKIN_CRON", "0 9 * * 1-5"))
    checkout_cron: str = field(default_factory=lambda: os.getenv("CHECKOUT_CRON", "0 18 * * 1-5"))

    # GPS 位置（必须与公司打卡范围一致）
    latitude: float = field(default_factory=lambda: float(os.getenv("LOCATION_LATITUDE", "39.9042")))
    longitude: float = field(default_factory=lambda: float(os.getenv("LOCATION_LONGITUDE", "116.4074")))
    address: str = field(default_factory=lambda: os.getenv("LOCATION_ADDRESS", ""))

    # 随机延迟（秒），模拟人工操作波动
    delay_min: int = field(default_factory=lambda: int(os.getenv("RANDOM_DELAY_MIN", "0")))
    delay_max: int = field(default_factory=lambda: int(os.getenv("RANDOM_DELAY_MAX", "300")))

    # Server 酱微信推送（可选）
    serverchan_key: str = field(default_factory=lambda: os.getenv("SERVERCHAN_KEY", ""))

    # 日志级别
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))

    def validate(self) -> None:
        """校验必填配置项"""
        if not self.dingtalk_token:
            raise ValueError(
                "DINGTALK_TOKEN 未配置。\n"
                "获取方式：打开 https://attend.dingtalk.com 并登录，\n"
                "按 F12 → Application → Cookies，复制 dingtalk_token 的值填入 .env"
            )
        if not self.dingtalk_user_id:
            raise ValueError(
                "DINGTALK_USER_ID 未配置。\n"
                "获取方式：登录钉钉后，在 Cookie 中找到 'empid' 字段，\n"
                "或在网络请求的响应体中查找 userId 字段填入 .env"
            )


# 全局单例
config = Config()
