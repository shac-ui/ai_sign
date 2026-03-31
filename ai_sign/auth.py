"""钉钉登录鉴权模块：模拟 APP 登录流程获取 access_token"""

import hashlib
import time
import httpx
from ai_sign.config import config
from ai_sign.logger import logger

# 钉钉 APP 端接口基础地址
_BASE_URL = "https://oapi.dingtalk.com"
# 钉钉 APP 登录接口（逆向自官方 APP，仅做学习研究用途）
_LOGIN_URL = "https://login.dingtalk.com/oauth2/challenge.htm"
_TOKEN_URL = "https://oapi.dingtalk.com/connect/token"

# 模拟 Android APP 的 User-Agent
_USER_AGENT = (
    "com.alibaba.android.rimet/7.6.10 "
    "(Linux; U; Android 12; zh-CN; Build/SKQ1.211006.001) "
    "AliApp(DingTalk/7.6.10) com.alibaba.wireless.security.open "
    "Weex/0.26.0.3 BREW"
)


def _md5(text: str) -> str:
    return hashlib.md5(text.encode()).hexdigest()


class DingTalkAuth:
    """管理登录态与 token 刷新"""

    def __init__(self) -> None:
        self._access_token: str = ""
        self._token_expire: float = 0.0
        self._client = httpx.Client(
            headers={"User-Agent": _USER_AGENT},
            timeout=15,
            follow_redirects=True,
            trust_env=False,  # 忽略系统代理环境变量，避免 SOCKS 代理依赖问题
        )

    @property
    def access_token(self) -> str:
        if not self._access_token or time.time() >= self._token_expire:
            self._refresh_token()
        return self._access_token

    def _refresh_token(self) -> None:
        """重新登录并刷新 token"""
        logger.info("正在刷新钉钉登录 token ...")
        try:
            payload = {
                "mobile": config.mobile,
                "password": _md5(config.password),
                "grant_type": "password",
                "client_id": "dingtalk",
                "client_secret": "dingtalk",
            }
            resp = self._client.post(_TOKEN_URL, data=payload)
            resp.raise_for_status()
            data = resp.json()

            if data.get("errcode", 0) != 0:
                raise RuntimeError(f"登录失败：{data.get('errmsg', '未知错误')}")

            self._access_token = data["access_token"]
            # token 有效期通常 7200 秒，提前 5 分钟刷新
            self._token_expire = time.time() + data.get("expires_in", 7200) - 300
            logger.info("钉钉 token 刷新成功")
        except httpx.HTTPError as exc:
            logger.error(f"网络请求失败：{exc}")
            raise

    def close(self) -> None:
        self._client.close()


# 模块级单例，供其他模块直接 import 使用
auth = DingTalkAuth()
