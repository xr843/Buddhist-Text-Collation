"""
认证API路由
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from datetime import datetime

from ....core.database import get_db
from ....core.auth import (
    create_access_token,
    create_refresh_token,
    verify_refresh_token,
    get_current_user,
    TokenData,
)
from ....core.security import verify_password, get_password_hash
from ....core.config import settings
from ....models.user import User, UserRole
from .schemas import (
    UserRegister,
    UserLogin,
    TokenRefresh,
    PasswordChange,
    UserUpdate,
    UserResponse,
    TokenResponse,
    MessageResponse,
)

router = APIRouter(prefix="/auth", tags=["认证"])


def create_user_response(user: User) -> UserResponse:
    """将User模型转换为UserResponse"""
    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        role=user.role.value if user.role else UserRole.USER.value,
        is_active=user.is_active,
        institution=user.institution,
        research_field=user.research_field,
        bio=user.bio,
        avatar_url=user.avatar_url,
        created_at=user.created_at,
        updated_at=user.updated_at,
        last_login=user.last_login,
    )


@router.post("/register", response_model=TokenResponse, summary="用户注册")
async def register(
    user_data: UserRegister,
    db: AsyncSession = Depends(get_db)
):
    """
    用户注册

    - **username**: 用户名（3-50字符，字母数字下划线中文）
    - **email**: 有效的邮箱地址
    - **password**: 密码（至少6字符）
    - **full_name**: 姓名（可选）
    - **institution**: 所属机构（可选）
    """
    # 检查用户名是否已存在
    result = await db.execute(
        select(User).where(User.username == user_data.username)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已被使用"
        )

    # 检查邮箱是否已存在
    result = await db.execute(
        select(User).where(User.email == user_data.email)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="邮箱已被注册"
        )

    # 创建新用户
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password,
        full_name=user_data.full_name,
        institution=user_data.institution,
        role=UserRole.USER,
        is_active=True,
        last_login=datetime.utcnow(),
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    # 生成令牌
    access_token = create_access_token(str(new_user.id))
    refresh_token = create_refresh_token(str(new_user.id))

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=create_user_response(new_user),
    )


@router.post("/login", response_model=TokenResponse, summary="用户登录")
async def login(
    login_data: UserLogin,
    db: AsyncSession = Depends(get_db)
):
    """
    用户登录

    - **username**: 用户名或邮箱
    - **password**: 密码
    """
    # 查找用户（支持用户名或邮箱登录）
    result = await db.execute(
        select(User).where(
            or_(
                User.username == login_data.username,
                User.email == login_data.username
            )
        )
    )
    user = result.scalar_one_or_none()

    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="账户已被禁用"
        )

    # 更新最后登录时间
    user.last_login = datetime.utcnow()
    await db.commit()
    await db.refresh(user)

    # 生成令牌
    access_token = create_access_token(str(user.id))
    refresh_token = create_refresh_token(str(user.id))

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=create_user_response(user),
    )


@router.post("/refresh", response_model=TokenResponse, summary="刷新令牌")
async def refresh_token(
    token_data: TokenRefresh,
    db: AsyncSession = Depends(get_db)
):
    """
    使用刷新令牌获取新的访问令牌
    """
    # 验证刷新令牌
    try:
        payload = verify_refresh_token(token_data.refresh_token)
    except HTTPException:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的刷新令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 获取用户
    user_id = int(payload.sub)
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="账户已被禁用"
        )

    # 生成新令牌
    access_token = create_access_token(str(user.id))
    new_refresh_token = create_refresh_token(str(user.id))

    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=create_user_response(user),
    )


@router.post("/logout", response_model=MessageResponse, summary="退出登录")
async def logout(
    token_data: TokenData = Depends(get_current_user)
):
    """
    退出登录

    注意：由于JWT是无状态的，服务端实际上不能"注销"令牌。
    客户端应该删除本地存储的令牌。
    """
    return MessageResponse(
        message="已退出登录",
        success=True
    )


@router.get("/me", response_model=UserResponse, summary="获取当前用户信息")
async def get_current_user_info(
    token_data: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取当前登录用户的详细信息
    """
    user_id = int(token_data.sub)
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )

    return create_user_response(user)


@router.put("/me", response_model=UserResponse, summary="更新用户信息")
async def update_current_user(
    update_data: UserUpdate,
    token_data: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    更新当前用户的个人信息
    """
    user_id = int(token_data.sub)
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )

    # 更新非空字段
    update_dict = update_data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        if hasattr(user, field):
            setattr(user, field, value)

    await db.commit()
    await db.refresh(user)

    return create_user_response(user)


@router.put("/password", response_model=MessageResponse, summary="修改密码")
async def change_password(
    password_data: PasswordChange,
    token_data: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    修改当前用户的密码
    """
    user_id = int(token_data.sub)
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )

    # 验证旧密码
    if not verify_password(password_data.old_password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="当前密码错误"
        )

    # 更新密码
    user.hashed_password = get_password_hash(password_data.new_password)
    await db.commit()

    return MessageResponse(
        message="密码修改成功",
        success=True
    )
