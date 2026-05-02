"""
安全相关配置和工具 - 增强版
"""
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status
import re
import os
from pathlib import Path

from .config import settings


# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """生成密码哈希"""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    创建访问令牌

    注意：推荐使用 app.core.auth.create_access_token 代替
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    secret_key = settings.SECRET_KEY.get_secret_value()
    encoded_jwt = jwt.encode(to_encode, secret_key, algorithm=settings.ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """
    创建刷新令牌

    注意：推荐使用 app.core.auth.create_refresh_token 代替
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    secret_key = settings.SECRET_KEY.get_secret_value()
    encoded_jwt = jwt.encode(to_encode, secret_key, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> dict:
    """
    解码令牌

    注意：推荐使用 app.core.auth.verify_token 代替
    """
    try:
        secret_key = settings.SECRET_KEY.get_secret_value()
        payload = jwt.decode(token, secret_key, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


def validate_file_extension(filename: str) -> bool:
    """
    验证文件扩展名

    Args:
        filename: 文件名

    Returns:
        是否为允许的扩展名
    """
    ext = Path(filename).suffix.lower()
    return ext in settings.ALLOWED_EXTENSIONS


def sanitize_filename(filename: str, max_length: int = 255) -> str:
    """
    清理文件名，防止路径遍历攻击和其他安全问题

    Args:
        filename: 原始文件名
        max_length: 最大文件名长度

    Returns:
        清理后的安全文件名

    安全措施：
    1. 移除路径分隔符和父目录引用
    2. 只保留安全字符（字母、数字、空格、点、下划线、连字符）
    3. 限制文件名长度
    4. 防止特殊文件名（如 .htaccess, web.config）
    """
    # 获取基本文件名（移除路径）
    filename = os.path.basename(filename)

    # 移除父目录引用
    filename = filename.replace('..', '')
    filename = filename.replace('./', '')
    filename = filename.replace('\\', '')

    # 只保留安全字符：字母、数字、中文、点、下划线、连字符、空格
    # 允许中文字符以支持中文文件名
    filename = re.sub(r'[^\w\s.\u4e00-\u9fff-]', '_', filename)

    # 移除多余的空格
    filename = re.sub(r'\s+', ' ', filename).strip()

    # 防止文件名只包含点（如 ".", "..", "..."）
    if re.match(r'^\.+$', filename):
        filename = 'file'

    # 防止以点开头的隐藏文件（Unix系统）
    if filename.startswith('.'):
        filename = '_' + filename[1:]

    # 限制文件名长度
    if len(filename) > max_length:
        # 保留扩展名
        name, ext = os.path.splitext(filename)
        max_name_length = max_length - len(ext)
        filename = name[:max_name_length] + ext

    # 确保文件名不为空
    if not filename:
        filename = 'unnamed_file'

    return filename


def validate_path(file_path: str, allowed_base: str) -> bool:
    """
    验证文件路径是否在允许的目录内

    防止路径遍历攻击

    Args:
        file_path: 要验证的文件路径
        allowed_base: 允许的基础目录

    Returns:
        路径是否安全
    """
    try:
        # 转换为绝对路径并规范化
        file_path = Path(file_path).resolve()
        allowed_base = Path(allowed_base).resolve()

        # 检查是否在允许的目录内
        return str(file_path).startswith(str(allowed_base))
    except (ValueError, OSError):
        return False


def sanitize_text_input(text: str, max_length: int = 10000) -> str:
    """
    清理文本输入，防止注入攻击

    Args:
        text: 原始文本
        max_length: 最大长度

    Returns:
        清理后的文本
    """
    # 限制长度
    if len(text) > max_length:
        text = text[:max_length]

    # 移除NULL字节
    text = text.replace('\x00', '')

    # 规范化换行符
    text = text.replace('\r\n', '\n').replace('\r', '\n')

    return text.strip()


def validate_url(url: str) -> bool:
    """
    验证URL格式

    Args:
        url: URL字符串

    Returns:
        是否为有效URL
    """
    # 简单的URL验证正则
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)

    return bool(url_pattern.match(url))


def generate_secure_token(length: int = 32) -> str:
    """
    生成安全的随机token

    Args:
        length: token长度

    Returns:
        URL安全的随机token
    """
    import secrets
    return secrets.token_urlsafe(length)


def check_password_strength(password: str) -> tuple[bool, list[str]]:
    """
    检查密码强度

    Args:
        password: 密码字符串

    Returns:
        (是否足够强, 错误消息列表)
    """
    errors = []

    if len(password) < 8:
        errors.append("密码长度至少8个字符")

    if not re.search(r'[A-Z]', password):
        errors.append("密码需要包含至少一个大写字母")

    if not re.search(r'[a-z]', password):
        errors.append("密码需要包含至少一个小写字母")

    if not re.search(r'\d', password):
        errors.append("密码需要包含至少一个数字")

    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        errors.append("密码需要包含至少一个特殊字符")

    return len(errors) == 0, errors


def mask_sensitive_data(data: str, visible_chars: int = 4) -> str:
    """
    遮蔽敏感数据（用于日志）

    Args:
        data: 敏感数据
        visible_chars: 显示的字符数

    Returns:
        遮蔽后的数据
    """
    if not data or len(data) <= visible_chars:
        return "***"

    return data[:visible_chars] + "***"

