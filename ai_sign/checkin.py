"""核心打卡模块：封装上班 / 下班打卡请求"""

import time
import random
import httpx
from typing import Literal
from ai_sign.config import config
from ai_sign.logger import logger
from ai_sign.auth import auth
from ai_sign.notify import send_notification

# 钉钉考勤打卡接口
_CHECKIN_URL = "https://oapi.dingtalk.com/attendance/record"

CheckType = Literal["OnDuty", "OffDuty"]


def _build_checkin_payload(check_type: CheckType) -> dict:
    """构造打卡请求体"""
    now = time.strftime("%Y-%m-%d %H:%M:%S")
    return {
        "access_token": auth.access_token,
        "userCheckTime": now,
        "locationMethod": "GPS",
        "checkType": check_type,
        "latitude": config.latitude,
        "longitude": config.longitude,
        "locationTitle": config.address,
        "locationDetail": config.address,
        "pbSourceType": 0,
    }


def _do_checkin(check_type: CheckType) -> bool:
    """执行一次打卡请求，返回是否成功"""
    action = "上班" if check_type == "OnDuty" else "下班"
    logger.info(f"开始执行 [{action}] 打卡 ...")

    # 随机延迟，模拟人工操作
    delay = random.randint(config.delay_min, config.delay_max)
    if delay > 0:
        logger.debug(f"随机延迟 {delay} 秒后打卡")
        time.sleep(delay)

    try:
        payload = _build_checkin_payload(check_type)
        with httpx.Client(timeout=15, trust_env=False) as client:
            resp = client.post(_CHECKIN_URL, json=payload)
            resp.raise_for_status()
            data = resp.json()

        if data.get("errcode", 0) == 0:
            logger.success(f"[{action}] 打卡成功！时间：{time.strftime('%Y-%m-%d %H:%M:%S')}")
            send_notification(f"✅ 钉钉{action}打卡成功", f"打卡时间：{time.strftime('%H:%M:%S')}")
            return True
        else:
            msg = data.get("errmsg", "未知错误")
            logger.error(f"[{action}] 打卡失败：{msg}")
            send_notification(f"❌ 钉钉{action}打卡失败", f"错误信息：{msg}")
            return False

    except httpx.HTTPError as exc:
        logger.error(f"[{action}] 打卡网络异常：{exc}")
        send_notification(f"❌ 钉钉{action}打卡网络异常", str(exc))
        return False


def checkin_on_duty() -> None:
    """上班打卡入口（由调度器调用）"""
    _do_checkin("OnDuty")


def checkout_off_duty() -> None:
    """下班打卡入口（由调度器调用）"""
    _do_checkin("OffDuty")
