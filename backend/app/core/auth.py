"""
认证和授权模块
支持JWT Token认证和API Key认证
"""
from datetime import datetime, timedelta
from typing import Optional
from fastapi import HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, APIKeyHeader
from jose import JWTError, jwt
from pydantic import BaseModel

from .config import settings


# ================================
# 安全方案定义
# ================================
# Bearer Token 认证 (JWT)
security_bearer = HTTPBearer(auto_error=False)

# API Key 认证
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


# ================================
# Token数据模型
# ================================
class TokenData(BaseModel):
    """Token载荷数据"""
    sub: Optional[str] = None  # 用户标识
    exp: Optional[datetime] = None  # 过期时间
    iat: Optional[datetime] = None  # 签发时间
    type: str = "access"  # token类型: access | refresh


class TokenResponse(BaseModel):
    """Token响应"""
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    expires_in: int  # 秒


# ================================
# Token 生成和验证
# ================================
def create_access_token(
    subject: str,
    expires_delta: Optional[timedelta] = None,
    additional_claims: Optional[dict] = None
) -> str:
    """
    创建访问令牌

    Args:
        subject: 用户标识（通常是user_id或username）
        expires_delta: 过期时间增量
        additional_claims: 额外的claims

    Returns:
        JWT token字符串
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode = {
        "sub": str(subject),
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access"
    }

    # 添加额外claims
    if additional_claims:
        to_encode.update(additional_claims)

    # 使用SecretStr的get_secret_value()方法获取实际的密钥
    secret_key = settings.SECRET_KEY.get_secret_value()
    encoded_jwt = jwt.encode(to_encode, secret_key, algorithm=settings.ALGORITHM)
    return encoded_jwt


def create_refresh_token(subject: str) -> str:
    """
    创建刷新令牌

    Args:
        subject: 用户标识

    Returns:
        JWT token字符串
    """
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    to_encode = {
        "sub": str(subject),
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "refresh"
    }

    secret_key = settings.SECRET_KEY.get_secret_value()
    encoded_jwt = jwt.encode(to_encode, secret_key, algorithm=settings.ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> TokenData:
    """
    验证并解码JWT token

    Args:
        token: JWT token字符串

    Returns:
        TokenData对象

    Raises:
        HTTPException: token无效或过期
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        secret_key = settings.SECRET_KEY.get_secret_value()
        payload = jwt.decode(token, secret_key, algorithms=[settings.ALGORITHM])

        subject: str = payload.get("sub")
        if subject is None:
            raise credentials_exception

        token_data = TokenData(
            sub=subject,
            exp=payload.get("exp"),
            iat=payload.get("iat"),
            type=payload.get("type", "access")
        )

        return token_data

    except JWTError:
        raise credentials_exception


def verify_refresh_token(token: str) -> TokenData:
    """
    验证刷新令牌

    Args:
        token: 刷新token字符串

    Returns:
        TokenData对象

    Raises:
        HTTPException: token无效或类型错误
    """
    token_data = verify_token(token)

    if token_data.type != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的刷新令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return token_data


# ================================
# API Key 验证
# ================================
def verify_api_key(api_key: Optional[str] = Security(api_key_header)) -> str:
    """
    验证API Key

    Args:
        api_key: API Key字符串

    Returns:
        验证通过的API Key

    Raises:
        HTTPException: API Key无效或未配置
    """
    # 如果未配置API_KEY，则跳过验证
    if not settings.API_KEY:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="API Key认证未启用"
        )

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="缺少API Key",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    expected_key = settings.API_KEY.get_secret_value()
    if api_key != expected_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无效的API Key"
        )

    return api_key


def require_api_key_if_configured(api_key: Optional[str] = Security(api_key_header)) -> Optional[str]:
    """
    如已配置 API_KEY，则强制要求请求携带匹配的 X-API-Key。
    如未配置（None 或空字符串），则放行（便于本地开发/单机使用）。
    """
    if not settings.API_KEY:
        return None

    expected = settings.API_KEY.get_secret_value()
    if not expected or not expected.strip():
        return None

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="缺少API Key",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    if api_key != expected:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无效的API Key"
        )

    return api_key


# ================================
# 依赖项：用于保护路由
# ================================
async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security_bearer)
) -> TokenData:
    """
    获取当前用户（通过JWT Token）

    使用方法:
    ```python
    @router.get("/protected")
    async def protected_route(current_user: TokenData = Depends(get_current_user)):
        return {"user": current_user.sub}
    ```

    Args:
        credentials: Bearer token凭据

    Returns:
        TokenData对象

    Raises:
        HTTPException: 未提供token或token无效
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="缺少认证凭据",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    return verify_token(token)


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security_bearer)
) -> Optional[TokenData]:
    """
    获取当前用户（可选，不强制要求认证）

    用于某些端点既可以匿名访问，也可以认证访问的场景

    Args:
        credentials: Bearer token凭据（可选）

    Returns:
        TokenData对象或None
    """
    if not credentials:
        return None

    try:
        token = credentials.credentials
        return verify_token(token)
    except HTTPException:
        return None


# ================================
# 混合认证：支持JWT和API Key
# ================================
async def get_current_user_or_api_key(
    bearer_credentials: Optional[HTTPAuthorizationCredentials] = Security(security_bearer),
    api_key: Optional[str] = Security(api_key_header)
) -> str:
    """
    混合认证：支持JWT Token或API Key

    优先使用JWT Token，如果没有则尝试API Key

    Args:
        bearer_credentials: Bearer token凭据
        api_key: API Key

    Returns:
        用户标识或"api_key"

    Raises:
        HTTPException: 两种认证方式都失败
    """
    # 尝试JWT Token
    if bearer_credentials:
        try:
            token_data = verify_token(bearer_credentials.credentials)
            return token_data.sub
        except HTTPException:
            pass

    # 尝试API Key
    if api_key and settings.API_KEY:
        try:
            verify_api_key(api_key)
            return "api_key"
        except HTTPException:
            pass

    # 两种都失败
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="需要有效的JWT Token或API Key",
        headers={"WWW-Authenticate": "Bearer"},
    )


# ================================
# 辅助函数
# ================================
def create_token_pair(subject: str) -> TokenResponse:
    """
    创建访问令牌和刷新令牌对

    Args:
        subject: 用户标识

    Returns:
        TokenResponse对象
    """
    access_token = create_access_token(subject)
    refresh_token = create_refresh_token(subject)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


def decode_token_without_verification(token: str) -> dict:
    """
    解码token但不验证（用于调试）

    警告：仅用于调试目的！

    Args:
        token: JWT token字符串

    Returns:
        token载荷
    """
    try:
        return jwt.get_unverified_claims(token)
    except JWTError:
        return {}
