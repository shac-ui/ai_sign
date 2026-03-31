"""定时调度模块：使用 APScheduler 按 cron 表达式触发打卡"""

import random
import time
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from ai_sign.config import config
from ai_sign.logger import logger


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


def _with_delay(fn):
    """装饰器：执行前随机延迟，模拟人工波动"""
    def wrapper(*args, **kwargs):
        delay = random.randint(config.delay_min, config.delay_max)
        if delay > 0:
            logger.info(f"随机延迟 {delay} 秒后执行打卡 ...")
            time.sleep(delay)
        return fn(*args, **kwargs)
    return wrapper


def _make_checkin_jobs():
    """根据 MODE 生成上班/下班打卡函数"""
    if config.mode == "app":
        from ai_sign.app_automation import do_app_checkin
        from ai_sign.notify import send_notification

        @_with_delay
        def checkin_on_duty():
            logger.info("【定时任务】上班打卡开始")
            ok = do_app_checkin()
            action = "上班"
            if ok:
                send_notification(f"✅ {action}打卡成功", f"时间：{time.strftime('%H:%M:%S')}")
            else:
                send_notification(f"❌ {action}打卡失败", "请检查日志")

        @_with_delay
        def checkout_off_duty():
            logger.info("【定时任务】下班打卡开始")
            ok = do_app_checkin()
            action = "下班"
            if ok:
                send_notification(f"✅ {action}打卡成功", f"时间：{time.strftime('%H:%M:%S')}")
            else:
                send_notification(f"❌ {action}打卡失败", "请检查日志")

    else:  # web 模式
        from ai_sign.checkin import checkin_on_duty, checkout_off_duty  # type: ignore

    return checkin_on_duty, checkout_off_duty


def start() -> None:
    """启动阻塞式调度器，直到进程被终止"""
    config.validate()

    checkin_on_duty, checkout_off_duty = _make_checkin_jobs()

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

    logger.info(f"调度器已启动（模式：{config.mode}）")
    logger.info(f"  上班打卡 cron：{config.checkin_cron}")
    logger.info(f"  下班打卡 cron：{config.checkout_cron}")
    if config.mode == "app":
        logger.info(f"  平台：{config.app_platform}")
        pkg = config.app_package or config.app_bundle_id
        logger.info(f"  目标 APP：{pkg}")
    logger.info(f"  随机延迟：{config.delay_min}~{config.delay_max} 秒")

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("调度器已停止")
