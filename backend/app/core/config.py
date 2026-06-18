"""
核心配置管理 - 优化版
支持多环境配置，增强安全性
"""
from pydantic_settings import BaseSettings
from pydantic import Field, SecretStr, validator
from typing import Optional, List
from enum import Enum
import os
import secrets
from pathlib import Path


class Environment(str, Enum):
    """环境类型"""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class Settings(BaseSettings):
    """应用配置"""

    # 环境配置
    ENV: Environment = Field(
        default=Environment.DEVELOPMENT,
        description="运行环境"
    )

    # 应用基础配置
    APP_NAME: str = "佛典智能标点与校勘研究平台"
    APP_VERSION: str = "3.1.0"
    API_V1_PREFIX: str = "/api/v1"
    DEBUG: bool = Field(
        default=False,
        description="调试模式（生产环境应为False）"
    )

    # 服务器配置
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # 数据库配置
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://buddhist_user:buddhist_pass@localhost:5432/buddhist_text",
        description="数据库连接URL"
    )
    DB_ECHO: bool = False  # 是否打印SQL语句
    DB_POOL_SIZE: int = Field(default=5, description="数据库连接池大小")
    DB_MAX_OVERFLOW: int = Field(default=10, description="数据库连接池最大溢出")

    # Redis配置
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_PASSWORD: Optional[str] = None
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # JWT和安全配置
    SECRET_KEY: SecretStr = Field(
        default_factory=lambda: SecretStr(secrets.token_urlsafe(32)),
        description="JWT密钥（生产环境必须通过环境变量设置）"
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # API密钥认证（可选）
    API_KEY: Optional[SecretStr] = Field(
        default=None,
        description="API密钥（用于服务间认证）"
    )

    # CORS配置（根据环境动态设置）
    BACKEND_CORS_ORIGINS: List[str] = Field(
        default_factory=list,
        description="允许的CORS源"
    )

    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v, values):
        """根据环境动态设置CORS"""
        if isinstance(v, str):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, list):
            return v

        # 如果未设置，根据环境返回默认值
        env = values.get("ENV", Environment.DEVELOPMENT)
        if env == Environment.PRODUCTION:
            return []  # 生产环境必须显式设置
        else:
            # 开发环境默认值；如需联通内网数字佛典平台，请通过
            # BACKEND_CORS_ORIGINS 环境变量补充对应来源。
            return [
                "http://localhost:3000",
                "http://localhost:5173",
            ]

    # 文本处理配置
    MAX_TEXT_LENGTH: int = 50000  # 单次处理最大字数
    ASYNC_THRESHOLD: int = 100000  # 异步处理阈值

    # 文件上传配置
    UPLOAD_DIR: Path = Path("uploads")
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS: set = {".txt", ".docx", ".pdf"}

    # 古籍酷（gj.cool）OCR 配置
    # 注：base_url / apiid 从古籍酷「账户设置」页获取（apiid 非用户名）
    OCR_ENABLED: bool = Field(default=True, description="是否启用古籍酷 OCR 集成（凭据未填则自动不可用）")
    GJCOOL_OCR_BASE_URL: str = Field(default="", description="识别 worker 端点 base（/ocr_pro），如 https://ap2.jzd.cool:9043；见账户『演示』页 OCR URL")
    GJCOOL_OCR_LOGIN_BASE_URL: str = Field(default="https://ocr.gj.cool", description="登录 base（/ocr_login，中心化认证）；留空则用 GJCOOL_OCR_BASE_URL")
    GJCOOL_OCR_APIID: str = Field(default="", description="古籍酷 apiid（账户页获取，非用户名）")
    GJCOOL_OCR_PASSWORD: SecretStr = Field(default=SecretStr(""), description="古籍酷账号密码")
    GJCOOL_OCR_VERIFY_SSL: bool = Field(default=True, description="是否校验 worker TLS 证书（worker 证书临时过期时设 false）")
    GJCOOL_OCR_TIMEOUT: int = Field(default=120, description="单次 OCR 请求超时（秒）")
    OCR_MAX_UPLOAD_SIZE: int = Field(default=20 * 1024 * 1024, description="OCR 上传图片大小上限（字节，默认 20MB）")
    OCR_ALLOWED_CONTENT_TYPES: List[str] = Field(
        default_factory=lambda: [
            "image/jpeg", "image/png", "image/tiff", "image/webp",
            "image/heic", "image/heif", "image/jp2", "image/avif",
        ],
        description="OCR 允许的图片 MIME 类型",
    )

    @property
    def ocr_configured(self) -> bool:
        """base_url / apiid / password 三者齐全才算已配置。"""
        return bool(
            self.GJCOOL_OCR_BASE_URL
            and self.GJCOOL_OCR_APIID
            and self.GJCOOL_OCR_PASSWORD.get_secret_value()
        )

    # 导出配置
    EXPORT_DIR: Path = Path("exports")
    EXPORT_EXPIRY_HOURS: int = 24  # 导出文件保留时间

    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/app.log"

    # 缓存配置
    CACHE_EXPIRE_SECONDS: int = 3600  # 1小时

    # 速率限制配置
    RATE_LIMIT_PER_MINUTE: int = Field(default=60, description="每分钟请求限制")
    RATE_LIMIT_ENABLED: bool = Field(default=True, description="是否启用速率限制")

    # 导入/下载配置（安全）
    IMPORT_IMAGE_ALLOWED_HOSTS: List[str] = Field(
        default_factory=list,
        description="允许导入图片下载的 host 白名单（为空表示不限制，仅建议内网/有鉴权环境使用）"
    )

    @validator("IMPORT_IMAGE_ALLOWED_HOSTS", pre=True)
    def assemble_import_image_allowed_hosts(cls, v):
        if isinstance(v, str):
            return [i.strip() for i in v.split(",") if i.strip()]
        if isinstance(v, list):
            return [str(i).strip() for i in v if str(i).strip()]
        return []

    # 安全配置
    ALLOWED_HOSTS: List[str] = Field(
        default_factory=lambda: ["*"],
        description="允许的主机名"
    )
    TRUST_PROXY_HEADERS: bool = Field(
        default=False,
        description="是否信任代理头（生产环境nginx后应为True）"
    )

    @validator("DEBUG")
    def validate_debug_in_production(cls, v, values):
        """生产环境禁止开启DEBUG"""
        env = values.get("ENV", Environment.DEVELOPMENT)
        if env == Environment.PRODUCTION and v:
            raise ValueError("生产环境不允许开启DEBUG模式")
        return v

    @validator("SECRET_KEY")
    def validate_secret_key_in_production(cls, v, values):
        """生产环境验证SECRET_KEY"""
        env = values.get("ENV", Environment.DEVELOPMENT)
        if env == Environment.PRODUCTION:
            # 确保生产环境的密钥足够长
            secret_value = v.get_secret_value() if isinstance(v, SecretStr) else v
            if len(secret_value) < 32:
                raise ValueError("生产环境SECRET_KEY长度必须至少32字符")
        return v

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# 创建全局配置实例
settings = Settings()

# 确保必要的目录存在
settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
settings.EXPORT_DIR.mkdir(parents=True, exist_ok=True)
Path("logs").mkdir(exist_ok=True)

# 日志配置验证
if settings.ENV == Environment.PRODUCTION:
    if settings.DEBUG:
        raise RuntimeError("生产环境不允许开启DEBUG模式")
    if not os.getenv("SECRET_KEY"):
        import warnings
        warnings.warn(
            "生产环境建议通过环境变量显式设置SECRET_KEY",
            RuntimeWarning
        )
