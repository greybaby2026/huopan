"""操作日志服务: 记录和查询"""
from datetime import datetime
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.operation_log import OperationLog


async def log_operation(
    db: AsyncSession,
    action: str,
    resource_type: str,
    user_id: int | None = None,
    username: str | None = None,
    resource_id: int | None = None,
    detail: str | None = None,
    ip: str | None = None,
) -> OperationLog:
    """记录一条操作日志"""
    log = OperationLog(
        user_id=user_id,
        username=username,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        detail=detail,
        ip=ip,
    )
    db.add(log)
    await db.flush()
    return log


async def query_logs(
    db: AsyncSession,
    page: int = 1,
    page_size: int = 50,
    action: str | None = None,
    resource_type: str | None = None,
    username: str | None = None,
) -> tuple[list[OperationLog], int]:
    """查询操作日志, 分页"""
    query = select(OperationLog)

    if action:
        query = query.where(OperationLog.action == action)
    if resource_type:
        query = query.where(OperationLog.resource_type == resource_type)
    if username:
        query = query.where(OperationLog.username.ilike(f"%{username}%"))

    # 总数
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    # 分页 + 时间倒序
    query = query.order_by(desc(OperationLog.created_at))
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    logs = result.scalars().all()
    return logs, total
