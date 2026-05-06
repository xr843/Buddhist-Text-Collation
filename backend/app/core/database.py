"""
数据库配置和连接管理 - 增强版
"""
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from typing import AsyncGenerator

from .config import settings, Environment
from .logging import logger


# 创建异步引擎
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DB_ECHO,
    future=True,
    pool_pre_ping=True,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_recycle=3600,  # 1小时回收连接
)

# 创建会话工厂
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


# 基础模型类
class Base(DeclarativeBase):
    """数据库模型基类"""
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    依赖注入：获取数据库会话

    使用方法：
    ```python
    from fastapi import Depends
    from app.core.database import get_db

    @router.get("/users")
    async def get_users(db: AsyncSession = Depends(get_db)):
        result = await db.execute(select(User))
        return result.scalars().all()
    ```
    """
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"数据库会话错误: {e}")
            raise
        finally:
            await session.close()


async def init_db():
    """
    初始化数据库（创建所有表）

    注意：生产环境应使用 Alembic 迁移
    """
    try:
        async with engine.begin() as conn:
            # 导入所有模型以确保它们被注册
            from app import models  # noqa: F401

            # 创建所有表（仅开发环境）
            if settings.ENV == Environment.DEVELOPMENT:
                await conn.run_sync(Base.metadata.create_all)
                logger.info("✅ 数据库表已创建（开发模式）")
            else:
                logger.info("生产环境，跳过自动创建表（请使用 Alembic）")

    except Exception as e:
        logger.error(f"初始化数据库失败: {e}")
        raise


async def close_db():
    """关闭数据库连接"""
    await engine.dispose()
    logger.info("✅ 数据库连接已关闭")
