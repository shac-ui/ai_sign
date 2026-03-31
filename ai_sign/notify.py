"""通知模块：通过 Server 酱将打卡结果推送到微信"""

import httpx
from ai_sign.config import config
from ai_sign.logger import logger


def send_notification(title: str, content: str) -> None:
    """推送消息到微信（需在 .env 中配置 SERVERCHAN_KEY）"""
    if not config.serverchan_key:
        logger.debug("未配置 SERVERCHAN_KEY，跳过微信通知")
        return

    url = f"https://sctapi.ftqq.com/{config.serverchan_key}.send"
    try:
        resp = httpx.post(url, data={"title": title, "desp": content}, timeout=10)
        resp.raise_for_status()
        result = resp.json()
        if result.get("code") == 0:
            logger.info(f"微信通知发送成功：{title}")
        else:
            logger.warning(f"微信通知发送失败：{result.get('message')}")
    except httpx.HTTPError as exc:
        logger.warning(f"微信通知网络异常（不影响打卡）：{exc}")
