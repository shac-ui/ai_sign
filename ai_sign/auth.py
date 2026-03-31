"""鉴权模块：基于 Cookie 的会话管理

钉钉没有公开的「手机号+密码直接换 token」API。
实际可行的方案是：用户手动登录一次浏览器版钉钉，
将 Cookie 中的 dingtalk_token 填入 .env，脚本携带该 Cookie 发起打卡请求。

Cookie 有效期约 7 天，过期后需重新登录并更新 .env。
"""

from ai_sign.config import config

# 钉钉 Web 端打卡接口使用的 Host
DINGTALK_WEB_HOST = "https://attend.dingtalk.com"


def get_auth_headers() -> dict:
    """构造携带鉴权 Cookie 的请求头，所有 HTTP 请求都应携带此头部"""
    cookie_parts = [f"dingtalk_token={config.dingtalk_token}"]

    # 如果用户还填了完整 Cookie 字符串，则优先使用
    cookie_str = config.dingtalk_cookie if config.dingtalk_cookie else "; ".join(cookie_parts)

    return {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36 DingTalk/7.6.10"
        ),
        "Cookie": cookie_str,
        "Content-Type": "application/json",
        "Referer": "https://attend.dingtalk.com/",
        "Origin": "https://attend.dingtalk.com",
    }
