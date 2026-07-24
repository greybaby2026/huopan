"""认证 API: 登录/注销/当前用户"""
from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.services.auth_service import authenticate_user, create_token, revoke_token, hash_password, get_token_user
from app.models.user import User, UserRole
from app.services.log_service import log_operation
from sqlalchemy import select

router = APIRouter(prefix="/auth", tags=["认证"])


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    token: str
    username: str
    display_name: str | None
    role: str


@router.post("/login", response_model=LoginResponse)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    user = await authenticate_user(db, data.username, data.password)
    if not user:
        raise HTTPException(401, "用户名或密码错误")
    token = await create_token(db, user)
    return LoginResponse(
        token=token,
        username=user.username,
        display_name=user.display_name,
        role=user.role.value,
    )


@router.post("/logout")
async def logout(
    authorization: str | None = Header(None),
    db: AsyncSession = Depends(get_db),
):
    # 注销当前 token
    if authorization and authorization.startswith("Bearer "):
        await revoke_token(db, authorization[7:])
    return {"message": "已注销"}


@router.get("/me")
async def get_me(user: dict = Depends(get_current_user)):
    return user


class UserCreate(BaseModel):
    username: str
    password: str
    display_name: str | None = None
    role: str = "sales"


@router.get("/users")
async def list_users(
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """列出所有用户 (仅管理员)"""
    if user.get("role") != UserRole.ADMIN.value:
        raise HTTPException(403, "仅管理员可查看用户列表")
    result = await db.execute(select(User))
    users = result.scalars().all()
    return {
        "items": [
            {
                "id": u.id,
                "username": u.username,
                "display_name": u.display_name,
                "role": u.role.value,
                "is_active": u.is_active,
                "assigned_customer_ids": u.assigned_customer_ids,
            }
            for u in users
        ]
    }


@router.post("/users")
async def create_user(
    data: UserCreate,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """创建用户 (仅管理员)"""
    if user.get("role") != UserRole.ADMIN.value:
        raise HTTPException(403, "仅管理员可创建用户")
    existing = await db.execute(select(User).where(User.username == data.username))
    if existing.scalar_one_or_none():
        raise HTTPException(409, f"用户名 {data.username} 已存在")
    try:
        role = UserRole(data.role)
    except ValueError:
        raise HTTPException(400, f"无效角色: {data.role}")
    new_user = User(
        username=data.username,
        password_hash=hash_password(data.password),
        display_name=data.display_name,
        role=role,
    )
    db.add(new_user)
    await db.flush()
    await db.refresh(new_user)

    # 操作日志
    from app.services.log_service import log_operation
    await log_operation(db, action="create", resource_type="user",
        user_id=user.get("user_id"), username=user.get("username"),
        resource_id=new_user.id, detail=f"创建用户: {data.username} ({data.role})")
    await db.commit()

    return {"id": new_user.id, "username": new_user.username, "role": new_user.role.value}


@router.put("/users/{user_id}")
async def update_user(
    user_id: int,
    data: UserCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """更新用户 (仅管理员)"""
    if current_user.get("role") != UserRole.ADMIN.value:
        raise HTTPException(403, "仅管理员可操作")
    target = await db.get(User, user_id)
    if not target:
        raise HTTPException(404, "用户不存在")
    target.display_name = data.display_name
    if data.password:
        from app.services.auth_service import hash_password
        target.password_hash = hash_password(data.password)
    try:
        target.role = UserRole(data.role)
    except ValueError:
        raise HTTPException(400, f"无效角色: {data.role}")

    await log_operation(db, action="update", resource_type="user",
        user_id=current_user.get("user_id"), username=current_user.get("username"),
        resource_id=user_id, detail=f"更新用户: {target.username}")
    await db.commit()
    return {"message": "已更新"}


@router.post("/users/{user_id}/toggle-active")
async def toggle_user_active(
    user_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """启用/停用用户 (仅管理员)"""
    if current_user.get("role") != UserRole.ADMIN.value:
        raise HTTPException(403, "仅管理员可操作")
    target = await db.get(User, user_id)
    if not target:
        raise HTTPException(404, "用户不存在")
    target.is_active = not target.is_active

    await log_operation(db, action="update", resource_type="user",
        user_id=current_user.get("user_id"), username=current_user.get("username"),
        resource_id=user_id, detail=f"{'启用' if target.is_active else '停用'}用户: {target.username}")
    await db.commit()
    return {"is_active": target.is_active}


@router.post("/init-admin")
async def init_admin(db: AsyncSession = Depends(get_db)):
    """初始化默认管理员账号 (首次部署用, 已有用户则拒绝)"""
    result = await db.execute(select(User).limit(1))
    if result.scalar_one_or_none():
        raise HTTPException(400, "系统已有用户, 请联系管理员创建账号")
    admin = User(
        username="admin",
        password_hash=hash_password("admin123"),
        display_name="管理员",
        role=UserRole.ADMIN,
    )
    db.add(admin)
    await db.commit()
    return {"message": "管理员账号已创建: admin / admin123 (请尽快修改密码)"}
