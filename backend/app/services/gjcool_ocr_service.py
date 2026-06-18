"""
古籍酷（gj.cool）OCR 服务

封装：登录拿 access_token（内存缓存，官方有效期 24h）+ 调用古籍 OCR `/ocr_pro`。
凭据（base_url / apiid / password）全部来自服务端配置（backend/.env），
绝不下发到前端——前端只把图片传给我们自己的 `/api/v1/ocr/recognize`。
"""
from __future__ import annotations

import time
from typing import Optional

import httpx

from app.core.config import settings
from app.core.logging import logger


class GjcoolOCRError(Exception):
    """OCR 调用相关错误，携带建议回给前端的 HTTP 状态码。"""

    def __init__(self, message: str, status_code: int = 502):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class GjcoolOCRService:
    """古籍酷 OCR 客户端：单例 httpx + access_token 内存缓存。"""

    _http_client: Optional[httpx.AsyncClient] = None
    _access_token: Optional[str] = None
    _token_expires_at: float = 0.0
    # access_token 官方有效期 24h；提前 5 分钟刷新，留安全边界
    _TOKEN_TTL_SECONDS = 24 * 3600 - 300

    @classmethod
    def is_configured(cls) -> bool:
        """凭据齐全且开关打开时才算可用。"""
        return settings.OCR_ENABLED and settings.ocr_configured

    @classmethod
    def _get_http_client(cls) -> httpx.AsyncClient:
        if cls._http_client is None or cls._http_client.is_closed:
            cls._http_client = httpx.AsyncClient(
                base_url=settings.GJCOOL_OCR_BASE_URL.rstrip("/"),
                timeout=httpx.Timeout(settings.GJCOOL_OCR_TIMEOUT, connect=10.0),
            )
        return cls._http_client

    @classmethod
    async def close_http_client(cls):
        if cls._http_client is not None and not cls._http_client.is_closed:
            await cls._http_client.aclose()
            cls._http_client = None

    @classmethod
    async def _login(cls) -> str:
        """登录获取 access_token 并缓存。"""
        client = cls._get_http_client()
        try:
            resp = await client.post(
                "/ocr_login",
                data={
                    "apiid": settings.GJCOOL_OCR_APIID,
                    "password": settings.GJCOOL_OCR_PASSWORD.get_secret_value(),
                    "encrypt": "0",
                    "is_long": "0",
                },
            )
        except httpx.HTTPError as e:
            raise GjcoolOCRError(f"无法连接古籍酷 OCR 服务: {e}", status_code=502)

        if resp.status_code != 200:
            # 不回显响应体，避免泄漏凭据相关信息到前端
            raise GjcoolOCRError(
                f"古籍酷 OCR 登录失败（HTTP {resp.status_code}），请检查 apiid/密码",
                status_code=502,
            )

        token = resp.json().get("access_token")
        if not token:
            raise GjcoolOCRError("古籍酷 OCR 登录响应缺少 access_token", status_code=502)

        cls._access_token = token
        cls._token_expires_at = time.time() + cls._TOKEN_TTL_SECONDS
        logger.info("✅ 古籍酷 OCR 登录成功，access_token 已缓存")
        return token

    @classmethod
    async def _ensure_token(cls, force: bool = False) -> str:
        if force or not cls._access_token or time.time() >= cls._token_expires_at:
            return await cls._login()
        return cls._access_token

    @classmethod
    async def recognize(cls, img_bytes: bytes, filename: str, content_type: str) -> dict:
        """
        对单张图片做古籍 OCR，返回精简结果：
        { text, char_number, line_number, width, height }
        其中 text 为按列分行整合后的识别文本（夹注用【】标注）。
        """
        if not cls.is_configured():
            raise GjcoolOCRError(
                "OCR 未配置：请在 backend/.env 填写古籍酷凭据", status_code=503
            )

        client = cls._get_http_client()

        async def _call(token: str) -> httpx.Response:
            return await client.post(
                "/ocr_pro",
                headers={"Authorization": f"gjcool {token}"},
                files={"img": (filename, img_bytes, content_type)},
            )

        token = await cls._ensure_token()
        try:
            resp = await _call(token)
            if resp.status_code == 401:
                # token 失效 → 强制重登一次再试
                logger.info("古籍酷 OCR 返回 401，刷新 token 后重试")
                token = await cls._ensure_token(force=True)
                resp = await _call(token)
        except httpx.HTTPError as e:
            raise GjcoolOCRError(f"古籍酷 OCR 请求失败: {e}", status_code=502)

        if resp.status_code != 200:
            raise GjcoolOCRError(
                f"古籍酷 OCR 识别失败（HTTP {resp.status_code}）", status_code=502
            )

        try:
            data = resp.json()
        except ValueError:
            raise GjcoolOCRError("古籍酷 OCR 返回非 JSON 响应", status_code=502)

        return {
            "text": data.get("text", ""),
            "char_number": data.get("CharNumber"),
            "line_number": data.get("LineNumber"),
            "width": data.get("Width"),
            "height": data.get("Height"),
        }
