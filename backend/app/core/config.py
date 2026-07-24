"""货盘系统配置 - 所有环境值通过 .env 注入，无硬编码"""
import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # 应用配置
    app_name: str = "令将货盘系统"
    app_version: str = "0.1.0"
    debug: bool = True

    # 数据库 - SQLite 起步，后续可改 PostgreSQL 连接串
    database_url: str = "sqlite+aiosqlite:///./huopan.db"

    # 文件存储
    upload_dir: str = str(Path(__file__).resolve().parent.parent.parent / "uploads")
    export_dir: str = str(Path(__file__).resolve().parent.parent.parent / "exports")

    # 图片限制
    max_image_size_mb: int = 10  # 单张图片最大 10MB
    allowed_image_types: tuple = ("jpg", "jpeg", "png", "webp")

    # 缩略图尺寸（像素），命名常量带注释
    THUMB_WIDTH: int = 300  # 缩略图宽度，列表展示用
    THUMB_QUALITY: int = 85  # 缩略图 JPEG 压缩质量

    # CORS - 内网部署，开发时允许 localhost
    cors_origins: tuple = ("http://localhost:5173", "http://localhost:3000")

    # 分页默认值
    DEFAULT_PAGE_SIZE: int = 20  # 列表默认每页条数
    MAX_PAGE_SIZE: int = 200  # 列表最大每页条数

    # 生产模式: 前端构建后由 FastAPI 托管, 只需穿透一个端口
    serve_frontend: bool = True  # 是否托管前端 SPA

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()

# 确保目录存在
Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
Path(settings.export_dir).mkdir(parents=True, exist_ok=True)
