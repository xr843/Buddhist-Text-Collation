"""
统一日志系统 - 基于Loguru
提供结构化日志、自动轮转、多级别输出
"""
import sys
from pathlib import Path
from loguru import logger
from typing import Optional

from .config import settings, Environment


# ================================
# 日志配置
# ================================
class LogConfig:
    """日志配置类"""

    def __init__(self):
        # 移除默认处理器
        logger.remove()

        # 根据环境配置不同的日志策略
        self._configure_console_logging()
        self._configure_file_logging()
        self._configure_error_logging()

        # 开发环境额外配置
        if settings.ENV == Environment.DEVELOPMENT:
            self._configure_debug_logging()

    def _configure_console_logging(self):
        """配置控制台日志输出"""
        # 根据环境选择不同的格式
        if settings.ENV == Environment.PRODUCTION:
            # 生产环境：JSON格式，便于日志收集系统解析
            format_string = (
                "{time:YYYY-MM-DD HH:mm:ss.SSS} | "
                "{level: <8} | "
                "{name}:{function}:{line} | "
                "{message}"
            )
            level = "INFO"
        else:
            # 开发环境：彩色格式，便于阅读
            format_string = (
                "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
                "<level>{level: <8}</level> | "
                "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
                "<level>{message}</level>"
            )
            level = settings.LOG_LEVEL

        logger.add(
            sys.stderr,
            format=format_string,
            level=level,
            colorize=True,
            backtrace=True,
            diagnose=settings.ENV != Environment.PRODUCTION,
        )

    def _configure_file_logging(self):
        """配置文件日志输出"""
        # 确保日志目录存在
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)

        # 主日志文件：所有INFO及以上级别
        logger.add(
            str(log_dir / "app_{time:YYYY-MM-DD}.log"),
            rotation="00:00",  # 每天午夜轮转
            retention="30 days",  # 保留30天
            compression="zip",  # 压缩旧日志
            format=(
                "{time:YYYY-MM-DD HH:mm:ss.SSS} | "
                "{level: <8} | "
                "{name}:{function}:{line} | "
                "{message}"
            ),
            level="INFO",
            encoding="utf-8",
            backtrace=True,
            diagnose=False,
        )

    def _configure_error_logging(self):
        """配置错误日志（单独文件）"""
        log_dir = Path("logs")

        # 错误日志：ERROR及以上级别
        logger.add(
            str(log_dir / "error_{time:YYYY-MM-DD}.log"),
            rotation="00:00",
            retention="90 days",  # 错误日志保留更久
            compression="zip",
            format=(
                "{time:YYYY-MM-DD HH:mm:ss.SSS} | "
                "{level: <8} | "
                "{name}:{function}:{line} | "
                "{message} | "
                "{extra}"
            ),
            level="ERROR",
            encoding="utf-8",
            backtrace=True,
            diagnose=True,
        )

    def _configure_debug_logging(self):
        """配置调试日志（开发环境）"""
        log_dir = Path("logs")

        # DEBUG日志：所有级别
        logger.add(
            str(log_dir / "debug_{time:YYYY-MM-DD}.log"),
            rotation="100 MB",  # 按大小轮转
            retention="7 days",  # 只保留7天
            compression="zip",
            format=(
                "{time:YYYY-MM-DD HH:mm:ss.SSS} | "
                "{level: <8} | "
                "{process.name}({process.id}) | "
                "{thread.name}({thread.id}) | "
                "{name}:{function}:{line} | "
                "{message} | "
                "{extra}"
            ),
            level="DEBUG",
            encoding="utf-8",
            backtrace=True,
            diagnose=True,
        )


# ================================
# 初始化日志配置
# ================================
log_config = LogConfig()


# ================================
# 导出logger实例
# ================================
__all__ = ["logger"]


# ================================
# 辅助函数
# ================================
def log_request(
    method: str,
    path: str,
    status_code: int,
    duration: float,
    user_id: Optional[str] = None,
):
    """
    记录HTTP请求日志

    Args:
        method: HTTP方法
        path: 请求路径
        status_code: 状态码
        duration: 处理时间（秒）
        user_id: 用户ID（可选）
    """
    logger.bind(
        request_method=method,
        request_path=path,
        status_code=status_code,
        duration_ms=round(duration * 1000, 2),
        user_id=user_id or "anonymous"
    ).info(
        f"{method} {path} {status_code} {duration*1000:.2f}ms"
    )


def log_ai_request(
    model: str,
    input_length: int,
    output_length: int,
    duration: float,
    success: bool = True,
):
    """
    记录AI请求日志

    Args:
        model: 模型名称
        input_length: 输入长度（字符/token）
        output_length: 输出长度
        duration: 处理时间（秒）
        success: 是否成功
    """
    logger.bind(
        ai_model=model,
        input_length=input_length,
        output_length=output_length,
        duration_sec=round(duration, 2),
        success=success
    ).info(
        f"AI请求: {model} | 输入{input_length} | 输出{output_length} | {duration:.2f}s"
    )


def log_error_with_context(
    error: Exception,
    context: dict,
    user_id: Optional[str] = None,
):
    """
    记录带上下文的错误

    Args:
        error: 异常对象
        context: 上下文信息
        user_id: 用户ID（可选）
    """
    logger.bind(
        error_type=type(error).__name__,
        user_id=user_id or "anonymous",
        **context
    ).exception(
        f"错误: {str(error)}"
    )


def log_security_event(
    event_type: str,
    severity: str,
    description: str,
    user_id: Optional[str] = None,
    ip_address: Optional[str] = None,
):
    """
    记录安全事件

    Args:
        event_type: 事件类型（如：failed_auth, suspicious_activity）
        severity: 严重程度（low, medium, high, critical）
        description: 事件描述
        user_id: 用户ID
        ip_address: IP地址
    """
    logger.bind(
        security_event=event_type,
        severity=severity,
        user_id=user_id or "anonymous",
        ip_address=ip_address or "unknown"
    ).warning(
        f"[安全事件] {event_type}: {description}"
    )


def log_performance_metric(
    metric_name: str,
    value: float,
    unit: str = "ms",
    tags: Optional[dict] = None,
):
    """
    记录性能指标

    Args:
        metric_name: 指标名称
        value: 指标值
        unit: 单位
        tags: 标签
    """
    extra_data = {
        "metric_name": metric_name,
        "value": value,
        "unit": unit
    }
    if tags:
        extra_data.update(tags)

    logger.bind(**extra_data).debug(
        f"[性能指标] {metric_name}: {value}{unit}"
    )
