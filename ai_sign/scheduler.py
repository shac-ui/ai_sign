"""定时调度模块：使用 APScheduler 按 cron 表达式触发打卡"""

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from ai_sign.config import config
from ai_sign.logger import logger
from ai_sign.checkin import checkin_on_duty, checkout_off_duty


def _parse_cron(expr: str) -> dict:
    """将 '分 时 日 月 周' 格式的 cron 表达式解析为 APScheduler 关键字参数"""
    parts = expr.strip().split()
    if len(parts) != 5:
        raise ValueError(f"无效的 cron 表达式：{expr}（应为 '分 时 日 月 周' 5 段格式）")
    minute, hour, day, month, day_of_week = parts
    return {
        "minute": minute,
        "hour": hour,
        "day": day,
        "month": month,
        "day_of_week": day_of_week,
    }


def start() -> None:
    """启动阻塞式调度器，直到进程被终止"""
    config.validate()

    scheduler = BlockingScheduler(timezone="Asia/Shanghai")

    checkin_kwargs = _parse_cron(config.checkin_cron)
    checkout_kwargs = _parse_cron(config.checkout_cron)

    scheduler.add_job(
        checkin_on_duty,
        trigger=CronTrigger(**checkin_kwargs, timezone="Asia/Shanghai"),
        id="checkin",
        name="上班打卡",
        replace_existing=True,
    )
    scheduler.add_job(
        checkout_off_duty,
        trigger=CronTrigger(**checkout_kwargs, timezone="Asia/Shanghai"),
        id="checkout",
        name="下班打卡",
        replace_existing=True,
    )

    logger.info(f"调度器已启动")
    logger.info(f"  上班打卡 cron：{config.checkin_cron}")
    logger.info(f"  下班打卡 cron：{config.checkout_cron}")
    logger.info(f"  打卡位置：{config.address}（{config.latitude}, {config.longitude}）")
    logger.info(f"  随机延迟：{config.delay_min}~{config.delay_max} 秒")

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("调度器已停止")
