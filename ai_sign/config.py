"""配置管理模块：从 .env 文件或环境变量加载所有运行时参数"""

import os
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()


def _env(key: str, default: str = "") -> str:
    return os.getenv(key, default)

def _env_int(key: str, default: int) -> int:
    return int(os.getenv(key, str(default)))

def _env_float(key: str, default: float) -> float:
    return float(os.getenv(key, str(default)))

def _env_bool(key: str, default: bool) -> bool:
    return os.getenv(key, str(default)).lower() in ("1", "true", "yes")

def _env_list(key: str) -> list[str]:
    """逗号分隔的字符串转列表"""
    val = os.getenv(key, "")
    return [x.strip() for x in val.split(",") if x.strip()]


@dataclass
class Config:
    # ------------------------------------------------------------------
    # 运行模式：web（Cookie 打卡）或 app（APP 自动化打卡）
    # ------------------------------------------------------------------
    mode: str = field(default_factory=lambda: _env("MODE", "app"))

    # ------------------------------------------------------------------
    # Web 模式：钉钉 Cookie（attend.dingtalk.com）
    # ------------------------------------------------------------------
    dingtalk_token: str = field(default_factory=lambda: _env("DINGTALK_TOKEN"))
    dingtalk_user_id: str = field(default_factory=lambda: _env("DINGTALK_USER_ID"))
    dingtalk_cookie: str = field(default_factory=lambda: _env("DINGTALK_COOKIE"))

    # Web 打卡 GPS 位置
    latitude: float = field(default_factory=lambda: _env_float("LOCATION_LATITUDE", 39.9042))
    longitude: float = field(default_factory=lambda: _env_float("LOCATION_LONGITUDE", 116.4074))
    address: str = field(default_factory=lambda: _env("LOCATION_ADDRESS"))

    # ------------------------------------------------------------------
    # APP 模式：移动端 UI 自动化
    # ------------------------------------------------------------------
    # 目标平台：android 或 ios
    app_platform: str = field(default_factory=lambda: _env("APP_PLATFORM", "android"))

    # Android 设备 serial（多设备时指定，单设备留空自动检测）
    device_serial: str = field(default_factory=lambda: _env("DEVICE_SERIAL"))

    # Android：目标 APP 包名，例如 com.example.checkin
    app_package: str = field(default_factory=lambda: _env("APP_PACKAGE"))
    # Android：目标 Activity（可留空，留空则启动默认 Activity）
    app_activity: str = field(default_factory=lambda: _env("APP_ACTIVITY"))

    # iOS：APP Bundle ID，例如 com.example.checkin
    app_bundle_id: str = field(default_factory=lambda: _env("APP_BUNDLE_ID"))
    # iOS：WDA 服务地址（默认 127.0.0.1:8100）
    wda_url: str = field(default_factory=lambda: _env("WDA_URL", "http://127.0.0.1:8100"))

    # APP 启动后等待页面加载的秒数
    app_launch_wait: float = field(default_factory=lambda: _env_float("APP_LAUNCH_WAIT", 3.0))

    # 打卡按钮定位（三选一，优先级：resource_id > text > xpath）
    # Android resource-id，例如 com.example.checkin:id/btn_punch
    checkin_resource_id: str = field(default_factory=lambda: _env("APP_CHECKIN_RESOURCE_ID"))
    # 按钮文字，例如 打卡、签到、上班打卡
    checkin_text: str = field(default_factory=lambda: _env("APP_CHECKIN_TEXT", "打卡"))
    # XPath 表达式（复杂布局时使用）
    checkin_xpath: str = field(default_factory=lambda: _env("APP_CHECKIN_XPATH"))

    # 打卡成功后页面出现的文字（用于验证，留空则不验证）
    success_text: str = field(default_factory=lambda: _env("APP_SUCCESS_TEXT"))

    # 需要自动关闭的弹窗按钮文字（逗号分隔），例如 我知道了,跳过,关闭
    popup_dismiss_texts: list = field(default_factory=lambda: _env_list("APP_POPUP_DISMISS"))

    # 查找元素的最大等待秒数
    element_find_timeout: float = field(default_factory=lambda: _env_float("APP_ELEMENT_TIMEOUT", 10.0))

    # 打卡结束后是否按 Home 键回到桌面
    go_home_after_checkin: bool = field(default_factory=lambda: _env_bool("APP_GO_HOME", True))

    # ------------------------------------------------------------------
    # 定时调度（cron 表达式：分 时 日 月 周）
    # ------------------------------------------------------------------
    checkin_cron: str = field(default_factory=lambda: _env("CHECKIN_CRON", "0 9 * * 1-5"))
    checkout_cron: str = field(default_factory=lambda: _env("CHECKOUT_CRON", "0 18 * * 1-5"))

    # 随机延迟（秒），模拟人工操作波动
    delay_min: int = field(default_factory=lambda: _env_int("RANDOM_DELAY_MIN", 0))
    delay_max: int = field(default_factory=lambda: _env_int("RANDOM_DELAY_MAX", 300))

    # ------------------------------------------------------------------
    # 通知 & 日志
    # ------------------------------------------------------------------
    serverchan_key: str = field(default_factory=lambda: _env("SERVERCHAN_KEY"))
    log_level: str = field(default_factory=lambda: _env("LOG_LEVEL", "INFO"))

    # ------------------------------------------------------------------
    def validate(self) -> None:
        """校验当前模式下的必填项"""
        if self.mode == "web":
            if not self.dingtalk_token:
                raise ValueError(
                    "Web 模式需要 DINGTALK_TOKEN。\n"
                    "获取方式：打开 https://attend.dingtalk.com 登录，\n"
                    "F12 → Application → Cookies → 复制 dingtalk_token 的值"
                )
            if not self.dingtalk_user_id:
                raise ValueError("Web 模式需要 DINGTALK_USER_ID（Cookie 中的 empid 字段）")

        elif self.mode == "app":
            platform = self.app_platform.lower()
            if platform == "android":
                if not self.app_package:
                    raise ValueError(
                        "APP 模式（Android）需要 APP_PACKAGE。\n"
                        "获取方式：adb shell dumpsys window | grep mCurrentFocus\n"
                        "打开目标打卡 APP 后运行上述命令即可看到包名"
                    )
            elif platform == "ios":
                if not self.app_bundle_id:
                    raise ValueError(
                        "APP 模式（iOS）需要 APP_BUNDLE_ID。\n"
                        "获取方式：tidevice applist | grep 打卡APP名称"
                    )
            else:
                raise ValueError(f"不支持的平台：{platform}，APP_PLATFORM 应为 android 或 ios")
        else:
            raise ValueError(f"不支持的运行模式：{self.mode}，MODE 应为 web 或 app")


# 全局单例
config = Config()
