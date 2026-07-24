"""用户认证服务: 密码哈希 + token 生成/验证"""
import hashlib
import secrets
import time
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.token import AuthToken
from app.models.user import User, UserRole


# token 过期时间 (秒), 8 小时
TOKEN_EXPIRY = 8 * 60 * 60


def hash_password(password: str) -> str:
    """SHA256 哈希密码"""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def verify_password(password: str, password_hash: str) -> bool:
    return hash_password(password) == password_hash


async def create_token(db: AsyncSession, user: User) -> str:
    """生成 token 并存入数据库"""
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
    """从数据库查询 token, 返回用户信息或 None"""
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
    """注销 token (软删除)"""
    result = await db.execute(select(AuthToken).where(AuthToken.token == token_str))
    token = result.scalar_one_or_none()
    if not token:
        return False
    token.is_active = False
    await db.commit()
    return True


async def authenticate_user(db: AsyncSession, username: str, password: str) -> User | None:
    """验证用户名密码, 返回 User 或 None"""
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user
