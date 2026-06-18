"""
FastAPI主应用 - 性能优化版
集成：速率限制、Redis缓存、流式响应、日志系统
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.logging import logger
from app.utils.cache import init_cache, close_cache
from app.middleware.rate_limit import setup_rate_limiting
from app.services.cbeta_service import CBETAService


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理

    启动时：
    - 初始化 Redis 缓存
    - 显示配置信息

    关闭时：
    - 关闭 Redis 连接
    """
    # 启动时执行
    logger.info(f"🚀 启动 {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"📝 运行环境: {settings.ENV.value}")
    logger.info(f"🔧 调试模式: {settings.DEBUG}")

    # 初始化 Redis 缓存
    try:
        await init_cache()
        logger.info("✅ Redis 缓存已初始化")
    except Exception as e:
        logger.warning(f"⚠️ Redis 缓存初始化失败（将降级运行）: {e}")

    # 性能优化提示
    if settings.RATE_LIMIT_ENABLED:
        logger.info(f"🛡️ 速率限制已启用: {settings.RATE_LIMIT_PER_MINUTE} 请求/分钟")
    else:
        logger.warning("⚠️ 速率限制已禁用")

    yield

    # 关闭时执行
    logger.info("👋 正在关闭应用...")

    # 关闭 CBETA HTTP 客户端
    try:
        await CBETAService.close_http_client()
        logger.info("✅ CBETA HTTP 客户端已关闭")
    except Exception as e:
        logger.error(f"❌ 关闭 CBETA HTTP 客户端失败: {e}")

    # 关闭古籍酷 OCR HTTP 客户端
    try:
        from app.services.gjcool_ocr_service import GjcoolOCRService
        await GjcoolOCRService.close_http_client()
        logger.info("✅ 古籍酷 OCR HTTP 客户端已关闭")
    except Exception as e:
        logger.error(f"❌ 关闭古籍酷 OCR HTTP 客户端失败: {e}")

    # 关闭 Redis 连接
    try:
        await close_cache()
        logger.info("✅ Redis 缓存已关闭")
    except Exception as e:
        logger.error(f"❌ 关闭 Redis 缓存失败: {e}")


# 创建FastAPI应用
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-Powered Platform for Buddhist Text Punctuation and Collation Research - Performance Optimized",
    lifespan=lifespan,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

# CORS中间件配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 配置速率限制
app = setup_rate_limiting(app)


# 根路径
@app.get("/")
async def root():
    """根路径"""
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "environment": settings.ENV.value,
        "features": {
            "rate_limiting": settings.RATE_LIMIT_ENABLED,
            "caching": True,  # Redis 缓存
            "streaming": True,  # 流式响应
            "authentication": True,  # API 认证
        },
        "docs": "/docs" if settings.DEBUG else "disabled in production"
    }


# 健康检查
@app.get("/health")
async def health_check():
    """
    健康检查端点

    检查：
    - 应用状态
    - Redis 缓存状态
    - AI 服务状态
    """
    from app.utils.cache import cache

    health_status = {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "environment": settings.ENV.value,
        "redis_cache": "connected" if cache._connected else "disconnected",
        "features": {
            "rate_limiting": settings.RATE_LIMIT_ENABLED,
            "streaming": True,
        }
    }

    return health_status


# 注册API路由（late import 故意：路由模块依赖上面 settings/middleware 的初始化）
from app.api.v1 import (  # noqa: E402
    auth,
    admin,
    collab,
    comparison,
    multi_collation,
    cbeta,
    export,
    commentary,
    sutra_commentary,
    sutra_reading,
    punctuation_transfer,
    citation,
    ocr,
)

# 认证API
app.include_router(
    auth.router,
    prefix=settings.API_V1_PREFIX,
    tags=["认证"]
)

# 管理员API
app.include_router(
    admin.router,
    prefix=settings.API_V1_PREFIX,
    tags=["管理员"]
)

# 协作项目API
app.include_router(
    collab.project_router,
    prefix=f"{settings.API_V1_PREFIX}/collab",
    tags=["协作"]
)
app.include_router(
    collab.share_router,
    prefix=f"{settings.API_V1_PREFIX}/collab",
    tags=["协作"]
)

# 文本对比API
app.include_router(
    comparison.router,
    prefix=f"{settings.API_V1_PREFIX}/comparison",
    tags=["对比"]
)

# 一底多校API（Demo版本）
app.include_router(
    multi_collation.router,
    prefix=f"{settings.API_V1_PREFIX}/multi-collation",
    tags=["一底多校"]
)

# CBETA平台对接API
app.include_router(
    cbeta.router,
    prefix=settings.API_V1_PREFIX,
    tags=["CBETA"]
)

# 导出API
app.include_router(
    export.router,
    prefix=settings.API_V1_PREFIX,
    tags=["导出"]
)

# 注疏引证API
app.include_router(
    commentary.router,
    prefix=f"{settings.API_V1_PREFIX}/multi-collation",
    tags=["注疏引证"]
)

# 经论-注疏关联API
app.include_router(
    sutra_commentary.router,
    prefix=f"{settings.API_V1_PREFIX}/sutra-commentary",
    tags=["经论-注疏关联"]
)

# 经论注释对读API
app.include_router(
    sutra_reading.router,
    prefix=settings.API_V1_PREFIX,
    tags=["经论注释对读"]
)

# 标点迁移API
app.include_router(
    punctuation_transfer.router,
    prefix=f"{settings.API_V1_PREFIX}/punctuation-transfer",
    tags=["标点迁移"]
)

# 引用与永久链接
app.include_router(
    citation.router,
    prefix=settings.API_V1_PREFIX,
    tags=["引用"]
)

# 古籍酷 OCR API
app.include_router(
    ocr.router,
    prefix=f"{settings.API_V1_PREFIX}/ocr",
    tags=["古籍OCR"]
)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )
