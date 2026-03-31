"""程序入口：支持常驻调度模式和单次手动打卡模式"""

import argparse
import os
from ai_sign.logger import logger


def _ensure_log_dir() -> None:
    os.makedirs("logs", exist_ok=True)


def run_scheduler() -> None:
    """启动定时打卡调度器（常驻进程）"""
    from ai_sign.scheduler import start
    start()


def run_once(check_type: str) -> None:
    """手动触发一次打卡，用于测试"""
    from ai_sign.config import config
    from ai_sign.checkin import checkin_on_duty, checkout_off_duty

    config.validate()
    if check_type == "on":
        logger.info("手动触发上班打卡")
        checkin_on_duty()
    elif check_type == "off":
        logger.info("手动触发下班打卡")
        checkout_off_duty()
    else:
        logger.error(f"未知的打卡类型：{check_type}，请使用 on 或 off")


def main() -> None:
    _ensure_log_dir()

    parser = argparse.ArgumentParser(
        description="钉钉辅助打卡工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例：
  python main.py                  # 启动定时调度器（常驻运行）
  python main.py --once on        # 立即执行一次上班打卡
  python main.py --once off       # 立即执行一次下班打卡
        """,
    )
    parser.add_argument(
        "--once",
        metavar="TYPE",
        choices=["on", "off"],
        help="手动触发单次打卡：on=上班，off=下班",
    )
    args = parser.parse_args()

    if args.once:
        run_once(args.once)
    else:
        run_scheduler()


if __name__ == "__main__":
    main()
