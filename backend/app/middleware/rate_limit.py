"""
速率限制中间件
使用 slowapi 实现灵活的速率限制
"""
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from typing import Callable
import time

from app.core.config import settings
from app.core.logging import logger, log_security_event


def get_identifier(request: Request) -> str:
    """
    获取请求标识符（用于速率限制）

    优先级：
    1. 用户ID（如果已认证）
    2. API Key（如果提供）
    3. IP地址
    """
    # 从请求状态中获取用户信息（如果已认证）
    if hasattr(request.state, "user") and request.state.user:
        identifier = f"user:{request.state.user}"
        logger.debug(f"速率限制标识: {identifier}")
        return identifier

    # 从 API Key 获取
    api_key = request.headers.get("X-API-Key")
    if api_key:
        identifier = f"apikey:{api_key[:8]}"  # 只使用前8个字符
        logger.debug(f"速率限制标识: {identifier}")
        return identifier

    # 默认使用IP地址
    ip = get_remote_address(request)
    logger.debug(f"速率限制标识: ip:{ip}")
    return ip


# 创建限流器实例
# 注意：如果 Redis 不可用，slowapi 会自动回退到内存存储
limiter = Limiter(
    key_func=get_identifier,
    default_limits=[f"{settings.RATE_LIMIT_PER_MINUTE}/minute"] if settings.RATE_LIMIT_ENABLED else [],
    enabled=settings.RATE_LIMIT_ENABLED,
    headers_enabled=True,  # 在响应头中包含限流信息
    # 不设置 storage_uri，使用默认的内存存储（更稳定）
    # storage_uri=settings.REDIS_URL if settings.RATE_LIMIT_ENABLED else None,
)


async def custom_rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """
    自定义速率限制异常处理

    记录安全事件并返回友好的错误信息
    """
    # 记录安全事件
    log_security_event(
        event_type="rate_limit_exceeded",
        severity="medium",
        description=f"速率限制触发: {request.url.path}",
        ip_address=get_remote_address(request)
    )

    # 安全地获取重试时间
    retry_after = "60"
    if hasattr(exc, 'detail') and exc.detail and "Retry after" in str(exc.detail):
        try:
            retry_after = str(exc.detail).split("Retry after ")[1].split(" ")[0]
        except (IndexError, AttributeError):
            pass

    # 返回详细的错误信息
    return JSONResponse(
        content={
            "error": "rate_limit_exceeded",
            "message": "请求过于频繁，请稍后再试",
            "retry_after": f"{retry_after} seconds",
            "limit": settings.RATE_LIMIT_PER_MINUTE,
            "window": "1 minute"
        },
        status_code=429,
        headers={
            "Retry-After": retry_after,
            "X-RateLimit-Limit": str(settings.RATE_LIMIT_PER_MINUTE),
            "X-RateLimit-Remaining": "0",
        }
    )


def setup_rate_limiting(app):
    """
    配置速率限制中间件

    Args:
        app: FastAPI 应用实例

    Returns:
        配置后的 app
    """
    if not settings.RATE_LIMIT_ENABLED:
        logger.warning("速率限制已禁用")
        return app

    # 注册限流器到应用状态
    app.state.limiter = limiter

    # 添加速率限制中间件
    app.add_middleware(SlowAPIMiddleware)

    # 注册自定义异常处理器
    app.add_exception_handler(RateLimitExceeded, custom_rate_limit_handler)

    logger.info(f"速率限制已启用: {settings.RATE_LIMIT_PER_MINUTE} 请求/分钟")

    return app


# 导出装饰器，用于在路由中使用
__all__ = ["limiter", "setup_rate_limiting"]
