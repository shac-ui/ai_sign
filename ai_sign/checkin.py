"""核心打卡模块：封装上班 / 下班打卡请求

钉钉 Web 考勤打卡接口（通过抓包 attend.dingtalk.com 获得）：
  POST https://attend.dingtalk.com/attend/h5/api/latest/punch/record

认证方式：Cookie 中携带 dingtalk_token
"""

import time
import random
import httpx
from typing import Literal
from ai_sign.config import config
from ai_sign.logger import logger
from ai_sign.auth import get_auth_headers, DINGTALK_WEB_HOST
from ai_sign.notify import send_notification

# 钉钉 Web 打卡接口
_PUNCH_URL = f"{DINGTALK_WEB_HOST}/attend/h5/api/latest/punch/record"

CheckType = Literal["OnDuty", "OffDuty"]


def _build_punch_payload(check_type: CheckType) -> dict:
    """构造 Web 端打卡请求体"""
    now_ms = int(time.time() * 1000)
    return {
        "userId": config.dingtalk_user_id,
        "checkType": check_type,
        "userCheckTime": now_ms,
        "locationMethod": "GPS",
        "latitude": config.latitude,
        "longitude": config.longitude,
        "locationTitle": config.address,
        "locationDetail": config.address,
        "pbSourceType": 0,
        "deviceId": "",
        "baseCheckTime": now_ms,
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
        payload = _build_punch_payload(check_type)
        headers = get_auth_headers()

        with httpx.Client(timeout=20, trust_env=False) as client:
            resp = client.post(_PUNCH_URL, json=payload, headers=headers)

        # Cookie 失效时通常返回 302 跳转登录页或 401
        if resp.status_code in (301, 302, 401, 403):
            logger.error(
                f"[{action}] 打卡失败：Cookie 已失效（HTTP {resp.status_code}），"
                "请重新登录 attend.dingtalk.com 并更新 .env 中的 DINGTALK_TOKEN"
            )
            send_notification(f"❌ 钉钉{action}打卡失败", "Cookie 已失效，请更新 DINGTALK_TOKEN")
            return False

        resp.raise_for_status()
        data = resp.json()

        # 接口正常响应时，success=true 或 errCode=0 表示成功
        success = data.get("success") is True or data.get("errCode") == 0
        if success:
            ts = time.strftime("%Y-%m-%d %H:%M:%S")
            logger.success(f"[{action}] 打卡成功！时间：{ts}")
            send_notification(f"✅ 钉钉{action}打卡成功", f"打卡时间：{time.strftime('%H:%M:%S')}")
            return True
        else:
            msg = data.get("errMsg") or data.get("message") or str(data)
            logger.error(f"[{action}] 打卡失败：{msg}")
            send_notification(f"❌ 钉钉{action}打卡失败", f"错误信息：{msg}")
            return False

    except httpx.HTTPStatusError as exc:
        logger.error(f"[{action}] 打卡 HTTP 错误：{exc.response.status_code} {exc.response.text[:200]}")
        send_notification(f"❌ 钉钉{action}打卡 HTTP 错误", str(exc))
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
