"""FastAPI 权限依赖: token 验证 + 角色检查"""
from fastapi import Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.auth_service import get_token_user
from app.models.user import UserRole


async def get_current_user(
    authorization: str | None = Header(None),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """从 Authorization header 提取 token, 返回用户信息 (数据库查询)"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "未提供认证 token")
    token = authorization[7:]
    user_info = await get_token_user(db, token)
    if not user_info:
        raise HTTPException(401, "token 无效或已过期")
    return user_info


async def get_current_user_optional(
    authorization: str | None = Header(None),
    db: AsyncSession = Depends(get_db),
) -> dict | None:
    """可选认证: 有 token 返回用户, 无 token 返回 None"""
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization[7:]
    return await get_token_user(db, token)
