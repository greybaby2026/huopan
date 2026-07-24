"""货盘系统 FastAPI 主应用"""
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse

from app.core.config import settings
from app.core.database import init_db
from app.api import products, customers, catalogs, exports, auth, logs, dicts


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动: 建表
    await init_db()
    yield


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态文件: 图片访问
app.mount("/uploads", StaticFiles(directory=settings.upload_dir), name="uploads")

# API 路由
app.include_router(products.router, prefix="/api/v1")
app.include_router(customers.router, prefix="/api/v1")
app.include_router(catalogs.router, prefix="/api/v1")
app.include_router(exports.router, prefix="/api/v1")
app.include_router(auth.router, prefix="/api/v1")
app.include_router(logs.router, prefix="/api/v1")
app.include_router(dicts.router, prefix="/api/v1")


@app.get("/health")
async def health():
    return {"status": "ok"}


# ---- 生产模式: 托管前端 SPA ----
# 前端 build 后 dist 目录路径
FRONTEND_DIST = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"

if FRONTEND_DIST.exists():
    # 挂载前端静态资源 (js/css/图片等)
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str, request: Request):
        """
        SPA catch-all: 非 API 路径返回 index.html, 让 vue-router 处理.
        """
        # 如果是 API 路径, 不处理 (让 FastAPI 返回 404)
        if full_path.startswith("api/") or full_path.startswith("uploads/") or full_path == "health":
            return HTMLResponse("Not Found", status_code=404)

        # 尝试返回具体静态文件
        file_path = FRONTEND_DIST / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path)

        # 其他路径返回 index.html (SPA fallback)
        index_path = FRONTEND_DIST / "index.html"
        if index_path.exists():
            return FileResponse(index_path)
        return HTMLResponse("Frontend not built. Run: cd frontend && npm run build", status_code=404)
else:
    @app.get("/")
    async def root():
        return {
            "app": settings.app_name,
            "version": settings.app_version,
            "docs": "/docs",
            "mode": "development (frontend not built)",
        }
