"""程序入口

支持三种运行方式：
  python main.py                   # 启动定时调度器（常驻运行）
  python main.py --once on         # 立即触发一次上班打卡
  python main.py --once off        # 立即触发一次下班打卡
  python main.py --inspect         # 打印当前手机屏幕元素，帮助配置打卡按钮
"""

import argparse
import os
import sys
import time


def _ensure_log_dir() -> None:
    os.makedirs("logs", exist_ok=True)


def run_scheduler() -> None:
    from ai_sign.scheduler import start
    start()


def run_once(check_type: str) -> None:
    from ai_sign.config import config
    config.validate()

    if config.mode == "app":
        from ai_sign.app_automation import do_app_checkin
        from ai_sign.notify import send_notification
        from ai_sign.logger import logger

        action = "上班" if check_type == "on" else "下班"
        logger.info(f"手动触发 [{action}] APP 打卡 ...")
        ok = do_app_checkin()
        if ok:
            logger.success(f"[{action}] 打卡成功")
            send_notification(f"✅ {action}打卡成功", f"时间：{time.strftime('%H:%M:%S')}")
        else:
            logger.error(f"[{action}] 打卡失败，请检查日志")
            send_notification(f"❌ {action}打卡失败", "请检查日志")
    else:
        from ai_sign.checkin import checkin_on_duty, checkout_off_duty
        if check_type == "on":
            checkin_on_duty()
        else:
            checkout_off_duty()


def run_inspect() -> None:
    """调用 tools/inspect_app.py 的逻辑，帮助定位打卡按钮"""
    from ai_sign.config import config

    # 动态导入 tools 目录下的 inspect_app
    import importlib.util
    tools_path = os.path.join(os.path.dirname(__file__), "tools", "inspect_app.py")
    if not os.path.exists(tools_path):
        print("tools/inspect_app.py 不存在")
        sys.exit(1)

    spec = importlib.util.spec_from_file_location("inspect_app", tools_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    platform = config.app_platform.lower()
    if platform == "android":
        module.inspect_android(config.device_serial or None)
    else:
        module.inspect_ios(config.wda_url)


def main() -> None:
    _ensure_log_dir()

    parser = argparse.ArgumentParser(
        description="辅助打卡工具 —— 定时自动打开打卡 APP 并完成打卡",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例：
  python main.py                  # 启动定时调度器（常驻运行）
  python main.py --once on        # 立即触发一次上班打卡
  python main.py --once off       # 立即触发一次下班打卡
  python main.py --inspect        # 打印手机当前页面元素，帮助配置打卡按钮定位

配置文件：复制 .env.example 为 .env 并填写参数
        """,
    )
    parser.add_argument(
        "--once",
        metavar="TYPE",
        choices=["on", "off"],
        help="手动触发单次打卡：on=上班，off=下班",
    )
    parser.add_argument(
        "--inspect",
        action="store_true",
        help="打印当前手机屏幕上的可点击元素，辅助配置打卡按钮",
    )
    args = parser.parse_args()

    if args.inspect:
        run_inspect()
    elif args.once:
        run_once(args.once)
    else:
        run_scheduler()


if __name__ == "__main__":
    main()
