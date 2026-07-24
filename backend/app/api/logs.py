"""操作日志 API: 查询和查看"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import UserRole
from app.services.log_service import query_logs

router = APIRouter(prefix="/logs", tags=["日志"])


@router.get("")
async def list_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    action: str | None = None,
    resource_type: str | None = None,
    username: str | None = None,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """查询操作日志 (仅管理员)"""
    if user.get("role") != UserRole.ADMIN.value:
        raise HTTPException(403, "仅管理员可查看日志")
    logs, total = await query_logs(
        db, page=page, page_size=page_size,
        action=action, resource_type=resource_type, username=username,
    )
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [
            {
                "id": log.id,
                "user_id": log.user_id,
                "username": log.username,
                "action": log.action,
                "resource_type": log.resource_type,
                "resource_id": log.resource_id,
                "detail": log.detail,
                "ip": log.ip,
                "created_at": log.created_at.isoformat() if log.created_at else None,
            }
            for log in logs
        ],
    }
