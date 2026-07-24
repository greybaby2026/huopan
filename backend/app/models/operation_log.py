"""操作日志模型"""
from datetime import datetime
from sqlalchemy import String, Text, Integer, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class OperationLog(Base):
    """操作日志"""
    __tablename__ = "operation_logs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int | None] = mapped_column(Integer, nullable=True, comment="操作用户ID")
    username: Mapped[str | None] = mapped_column(String(64), nullable=True, comment="用户名")
    action: Mapped[str] = mapped_column(String(64), nullable=False, index=True, comment="操作: create/update/delete/export")
    resource_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True, comment="资源类型: product/customer/catalog/user")
    resource_id: Mapped[int | None] = mapped_column(Integer, nullable=True, comment="资源ID")
    detail: Mapped[str | None] = mapped_column(Text, nullable=True, comment="操作详情(JSON)")
    ip: Mapped[str | None] = mapped_column(String(64), nullable=True, comment="操作IP")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

    def __repr__(self):
        return f"<OperationLog {self.action} {self.resource_type}#{self.resource_id}>"
