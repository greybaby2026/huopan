"""用户与权限模型"""
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import String, DateTime, Boolean, Enum, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class UserRole(str, PyEnum):
    """用户角色枚举"""
    ADMIN = "admin"        # 管理员: 全权
    SALES = "sales"        # 业务员: 自己的客户货盘
    WAREHOUSE = "warehouse"  # 仓库: 只读 + 库存管理


class User(Base):
    """系统用户表"""
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(256), nullable=False, comment="密码哈希")
    display_name: Mapped[str | None] = mapped_column(String(64), nullable=True, comment="显示名")
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.SALES, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # 业务员关联的客户 (仅 sales 角色用)
    assigned_customer_ids: Mapped[str | None] = mapped_column(
        String(512), nullable=True, comment="关联客户ID, 逗号分隔"
    )

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<User {self.username} role={self.role}>"
