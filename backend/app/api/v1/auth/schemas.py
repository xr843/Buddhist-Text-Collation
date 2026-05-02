"""
认证相关的请求/响应模型
"""
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
from datetime import datetime
import re


class UserRegister(BaseModel):
    """用户注册请求"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    email: EmailStr = Field(..., description="邮箱地址")
    password: str = Field(..., min_length=6, max_length=128, description="密码")
    full_name: Optional[str] = Field(None, max_length=100, description="姓名")
    institution: Optional[str] = Field(None, max_length=200, description="所属机构")

    @validator("username")
    def validate_username(cls, v):
        if not re.match(r'^[a-zA-Z0-9_\u4e00-\u9fff]+$', v):
            raise ValueError("用户名只能包含字母、数字、下划线和中文")
        return v

    @validator("password")
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError("密码长度至少6个字符")
        return v


class UserLogin(BaseModel):
    """用户登录请求"""
    username: str = Field(..., description="用户名或邮箱")
    password: str = Field(..., description="密码")


class TokenRefresh(BaseModel):
    """刷新Token请求"""
    refresh_token: str = Field(..., description="刷新令牌")


class PasswordChange(BaseModel):
    """修改密码请求"""
    old_password: str = Field(..., description="旧密码")
    new_password: str = Field(..., min_length=6, max_length=128, description="新密码")

    @validator("new_password")
    def validate_new_password(cls, v, values):
        if "old_password" in values and v == values["old_password"]:
            raise ValueError("新密码不能与旧密码相同")
        return v


class UserUpdate(BaseModel):
    """用户信息更新请求"""
    full_name: Optional[str] = Field(None, max_length=100, description="姓名")
    institution: Optional[str] = Field(None, max_length=200, description="所属机构")
    research_field: Optional[str] = Field(None, max_length=200, description="研究领域")
    bio: Optional[str] = Field(None, max_length=2000, description="个人简介")
    avatar_url: Optional[str] = Field(None, max_length=500, description="头像URL")


class UserResponse(BaseModel):
    """用户信息响应"""
    id: int
    username: str
    email: str
    full_name: Optional[str] = None
    role: str
    is_active: bool
    institution: Optional[str] = None
    research_field: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """Token响应"""
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    expires_in: int  # 秒
    user: UserResponse


class MessageResponse(BaseModel):
    """通用消息响应"""
    message: str
    success: bool = True
