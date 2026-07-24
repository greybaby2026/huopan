"""认证 Token 模型 - 持久化 token, 重启不丢失"""
from datetime import datetime
from sqlalchemy import String, Text, Integer, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class AuthToken(Base):
    """持久化 token 表"""
    __tablename__ = "auth_tokens"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    token: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False, comment="token 值")
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, comment="用户ID")
    username: Mapped[str] = mapped_column(String(64), nullable=False, comment="用户名")
    display_name: Mapped[str | None] = mapped_column(String(64), nullable=True, comment="显示名")
    role: Mapped[str] = mapped_column(String(32), nullable=False, comment="角色")
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, comment="过期时间")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, comment="是否有效")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<AuthToken user={self.username} expires={self.expires_at}>"
