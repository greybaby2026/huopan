"""用户认证服务: bcrypt 密码哈希 + token 生成/验证"""
import secrets
import time
from datetime import datetime

import bcrypt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.token import AuthToken
from app.models.user import User, UserRole


# token 过期时间 (秒), 8 小时
TOKEN_EXPIRY = 8 * 60 * 60


def hash_password(password: str) -> str:
    """使用 bcrypt 哈希密码 (自动加盐).

    Args:
        password: 明文密码.

    Returns:
        bcrypt 哈希字符串 (含 salt, 可直接存数据库).

    Note:
        bcrypt 自带随机 salt, 每次哈希结果不同, 无需单独存 salt.
        cost factor 默认 12, 约 250ms/次, 兼顾安全与性能.
    """
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    """验证密码是否匹配 bcrypt 哈希.

    Args:
        password: 用户输入的明文密码.
        password_hash: 数据库中存储的 bcrypt 哈希.

    Returns:
        True 如果密码匹配.
    """
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except (ValueError, TypeError):
        # 哈希格式无效 (如旧 SHA256 哈希), 返回 False 触发重新设置密码
        return False


async def create_token(db: AsyncSession, user: User) -> str:
    """生成 token 并存入数据库.

    Args:
        db: 异步数据库会话.
        user: 已通过认证的 User 对象.

    Returns:
        token 字符串 (URL-safe, 32 字节随机).
    """
    token_str = secrets.token_urlsafe(32)
    token = AuthToken(
        token=token_str,
        user_id=user.id,
        username=user.username,
        display_name=user.display_name,
        role=user.role.value if isinstance(user.role, UserRole) else user.role,
        expires_at=datetime.utcfromtimestamp(time.time() + TOKEN_EXPIRY),
    )
    db.add(token)
    await db.commit()
    return token_str


async def get_token_user(db: AsyncSession, token_str: str) -> dict | None:
    """从数据库查询 token, 返回用户信息或 None.

    Args:
        db: 异步数据库会话.
        token_str: 客户端传来的 token 字符串.

    Returns:
        用户信息字典, 包含 user_id/username/display_name/role/expires_at.
        token 无效或过期则返回 None.
    """
    result = await db.execute(
        select(AuthToken).where(
            AuthToken.token == token_str,
            AuthToken.expires_at > datetime.utcnow(),
            AuthToken.is_active == True,
        )
    )
    token = result.scalar_one_or_none()
    if not token:
        return None
    return {
        "user_id": token.user_id,
        "username": token.username,
        "display_name": token.display_name,
        "role": token.role,
        "expires_at": token.expires_at.timestamp(),
    }


async def revoke_token(db: AsyncSession, token_str: str) -> bool:
    """注销 token (软删除, 标记 is_active=False).

    Args:
        db: 异步数据库会话.
        token_str: 要注销的 token.

    Returns:
        True 如果成功注销, False 如果 token 不存在.
    """
    result = await db.execute(select(AuthToken).where(AuthToken.token == token_str))
    token = result.scalar_one_or_none()
    if not token:
        return False
    token.is_active = False
    await db.commit()
    return True


async def authenticate_user(db: AsyncSession, username: str, password: str) -> User | None:
    """验证用户名密码.

    Args:
        db: 异步数据库会话.
        username: 用户名.
        password: 明文密码.

    Returns:
        User 对象如果认证成功, 否则 None.
    """
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user
