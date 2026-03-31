"""APP 自动化打卡核心模块

支持两种平台：
  - Android：通过 uiautomator2 + ADB 控制手机
  - iOS：通过 facebook-wda + tidevice 控制手机

使用前提：
  Android：
    1. 手机开启「开发者选项」→「USB 调试」（或无线调试）
    2. pip install uiautomator2
    3. 首次连接执行：python -m uiautomator2 init（向手机推送 agent）

  iOS：
    1. 手机安装 WebDriverAgent（需 Xcode 签名或企业证书）
    2. pip install facebook-wda tidevice
    3. tidevice wdaproxy -B com.facebook.wda.WebDriverAgent.Runner
"""

import time
from typing import Optional
from ai_sign.config import config
from ai_sign.logger import logger


# ---------------------------------------------------------------------------
# Android 实现（uiautomator2）
# ---------------------------------------------------------------------------

class AndroidCheckin:
    """使用 uiautomator2 控制 Android 手机完成 APP 打卡"""

    def __init__(self) -> None:
        try:
            import uiautomator2 as u2
            self._u2 = u2
        except ImportError:
            raise ImportError(
                "请先安装 Android 自动化依赖：pip install uiautomator2\n"
                "首次使用还需执行：python -m uiautomator2 init"
            )

    def connect(self):
        """连接设备（USB 或无线）"""
        serial = config.device_serial
        if serial:
            logger.info(f"连接 Android 设备：{serial}")
            d = self._u2.connect(serial)
        else:
            logger.info("自动检测并连接 Android 设备 ...")
            d = self._u2.connect()
        info = d.info
        logger.info(f"已连接：{info.get('productName', 'Unknown')}  Android {info.get('sdkInt', '?')}")
        return d

    def checkin(self) -> bool:
        """执行完整的打卡流程：启动 APP → 导航到打卡页 → 点击打卡按钮"""
        d = self.connect()
        try:
            return self._do_checkin(d)
        finally:
            # 打卡完成后按 Home 键回到桌面
            if config.go_home_after_checkin:
                d.press("home")

    def _do_checkin(self, d) -> bool:
        pkg = config.app_package
        activity = config.app_activity

        # 1. 启动目标 APP
        logger.info(f"启动 APP：{pkg}")
        if activity:
            d.app_start(pkg, activity, wait=True, stop=True)
        else:
            d.app_start(pkg, wait=True, stop=True)
        time.sleep(config.app_launch_wait)

        # 2. 关闭可能弹出的权限/广告弹窗
        self._dismiss_popups(d)

        # 3. 通过 resource-id / text / xpath 找到打卡按钮并点击
        btn = self._find_checkin_button(d)
        if btn is None:
            logger.error("未找到打卡按钮，请检查 APP_CHECKIN_* 配置或运行 inspect 工具定位元素")
            return False

        logger.info(f"找到打卡按钮，准备点击 ...")
        btn.click()
        time.sleep(2)

        # 4. 检测打卡成功标志（可选）
        return self._verify_success(d)

    def _dismiss_popups(self, d) -> None:
        """关闭常见弹窗（权限申请、更新提示、广告）"""
        dismiss_texts = config.popup_dismiss_texts
        if not dismiss_texts:
            return
        for text in dismiss_texts:
            try:
                if d(text=text).exists(timeout=1):
                    d(text=text).click()
                    logger.debug(f"关闭弹窗：{text}")
                    time.sleep(0.5)
            except Exception:
                pass

    def _find_checkin_button(self, d):
        """按优先级查找打卡按钮元素"""
        timeout = config.element_find_timeout

        # 优先使用 resource-id（最稳定）
        if config.checkin_resource_id:
            elem = d(resourceId=config.checkin_resource_id)
            if elem.exists(timeout=timeout):
                return elem

        # 其次使用 text 匹配
        if config.checkin_text:
            elem = d(text=config.checkin_text)
            if elem.exists(timeout=timeout):
                return elem
            # 尝试 textContains
            elem = d(textContains=config.checkin_text)
            if elem.exists(timeout=timeout):
                return elem

        # 最后使用 xpath（灵活但性能稍差）
        if config.checkin_xpath:
            elem = d.xpath(config.checkin_xpath)
            if elem.exists(timeout=timeout):
                return elem

        return None

    def _verify_success(self, d) -> bool:
        """检测打卡成功提示，没有配置则默认认为成功"""
        if not config.success_text:
            logger.info("未配置成功验证文本，默认视为打卡成功")
            return True

        if d(textContains=config.success_text).exists(timeout=5):
            logger.success(f"检测到成功标志：「{config.success_text}」")
            return True
        else:
            logger.warning(f"未检测到成功标志「{config.success_text}」，打卡结果不确定，请手动确认")
            return False


# ---------------------------------------------------------------------------
# iOS 实现（facebook-wda + tidevice）
# ---------------------------------------------------------------------------

class IOSCheckin:
    """使用 facebook-wda 控制 iOS 手机完成 APP 打卡"""

    def __init__(self) -> None:
        try:
            import wda
            self._wda = wda
        except ImportError:
            raise ImportError(
                "请先安装 iOS 自动化依赖：\n"
                "  pip install facebook-wda tidevice\n"
                "并启动 WDA 代理：\n"
                "  tidevice wdaproxy -B com.facebook.wda.WebDriverAgent.Runner --port 8100"
            )

    def connect(self):
        wda_url = config.wda_url or "http://127.0.0.1:8100"
        logger.info(f"连接 WDA：{wda_url}")
        c = self._wda.Client(wda_url)
        # 验证连接
        status = c.status()
        logger.info(f"WDA 已连接，sessionId：{status.get('sessionId', 'N/A')}")
        return c

    def checkin(self) -> bool:
        c = self.connect()
        try:
            return self._do_checkin(c)
        finally:
            if config.go_home_after_checkin:
                c.home()

    def _do_checkin(self, c) -> bool:
        bundle_id = config.app_bundle_id
        if not bundle_id:
            raise ValueError("iOS 打卡需要配置 APP_BUNDLE_ID，例如：com.example.checkinapp")

        # 1. 激活（前台启动）目标 APP
        logger.info(f"激活 APP：{bundle_id}")
        c.session().app_activate(bundle_id)
        time.sleep(config.app_launch_wait)

        s = c.session()

        # 2. 关闭弹窗
        for text in (config.popup_dismiss_texts or []):
            try:
                elem = s(name=text)
                if elem.exists:
                    elem.tap()
                    time.sleep(0.5)
            except Exception:
                pass

        # 3. 查找打卡按钮
        btn = self._find_checkin_button(s)
        if btn is None:
            logger.error("未找到打卡按钮，请检查 APP_CHECKIN_* 配置")
            return False

        logger.info("找到打卡按钮，准备点击 ...")
        btn.tap()
        time.sleep(2)

        return self._verify_success(s)

    def _find_checkin_button(self, s):
        timeout = config.element_find_timeout

        if config.checkin_text:
            try:
                elem = s(name=config.checkin_text)
                if elem.wait(timeout=timeout):
                    return elem
                elem = s(label=config.checkin_text)
                if elem.wait(timeout=timeout):
                    return elem
            except Exception:
                pass

        if config.checkin_xpath:
            try:
                elem = s.xpath(config.checkin_xpath)
                if elem.wait(timeout=timeout):
                    return elem
            except Exception:
                pass

        return None

    def _verify_success(self, s) -> bool:
        if not config.success_text:
            logger.info("未配置成功验证文本，默认视为打卡成功")
            return True

        try:
            if s(nameContains=config.success_text).wait(timeout=5):
                logger.success(f"检测到成功标志：「{config.success_text}」")
                return True
        except Exception:
            pass

        logger.warning(f"未检测到成功标志「{config.success_text}」，打卡结果不确定，请手动确认")
        return False


# ---------------------------------------------------------------------------
# 统一工厂函数
# ---------------------------------------------------------------------------

def create_checkin_driver():
    """根据配置选择 Android 或 iOS 驱动"""
    platform = (config.app_platform or "android").lower()
    if platform == "android":
        return AndroidCheckin()
    elif platform == "ios":
        return IOSCheckin()
    else:
        raise ValueError(f"不支持的平台：{platform}，请设置 APP_PLATFORM=android 或 APP_PLATFORM=ios")


def do_app_checkin() -> bool:
    """完整的 APP 打卡流程入口（由调度器或 main 调用）"""
    driver = create_checkin_driver()
    return driver.checkin()
