"""图片处理服务: 缩略图生成 + 水印"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import uuid

from app.core.config import settings


def save_upload_image(file_bytes: bytes, original_filename: str) -> tuple[str, str]:
    """
    保存上传图片, 同时生成缩略图.
    返回 (original_path, thumbnail_path), 均为相对 upload_dir 的路径.
    """
    ext = Path(original_filename).suffix.lower().lstrip(".")
    if ext not in settings.allowed_image_types:
        raise ValueError(f"不支持的图片格式: {ext}, 仅支持 {settings.allowed_image_types}")

    unique_name = f"{uuid.uuid4().hex}.{ext}"
    original_rel = unique_name
    original_full = Path(settings.upload_dir) / original_rel

    original_full.write_bytes(file_bytes)

    # 生成缩略图
    thumb_rel = f"thumb_{unique_name}"
    thumb_full = Path(settings.upload_dir) / thumb_rel

    try:
        img = Image.open(original_full)
        img.thumbnail((settings.THUMB_WIDTH, settings.THUMB_WIDTH))
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        thumb_path_jpg = Path(settings.upload_dir) / f"thumb_{Path(unique_name).stem}.jpg"
        img.save(thumb_path_jpg, "JPEG", quality=settings.THUMB_QUALITY)
        thumb_rel = f"thumb_{Path(unique_name).stem}.jpg"
    except Exception:
        thumb_rel = original_rel

    return original_rel, thumb_rel


# 水印文字常量
WATERMARK_TEXT = "令将货盘"  # 品牌水印文字
WATERMARK_FONT_SIZE = 36  # 水印字体大小
WATERMARK_OPACITY = 80  # 水印透明度 (0-255)


def add_watermark(input_path: str | Path, output_path: str | Path) -> None:
    """
    给图片添加品牌水印, 保存到 output_path.
    水印为半透明斜文字, 平铺整张图.
    """
    img = Image.open(input_path).convert("RGBA")

    # 创建水印层
    watermark_layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(watermark_layer)

    # 尝试加载字体, 失败则用默认
    font = None
    font_paths = [
        "C:/Windows/Fonts/msyh.ttc",     # 微软雅黑
        "C:/Windows/Fonts/simhei.ttf",    # 黑体
        "C:/Windows/Fonts/arial.ttf",     # Arial
    ]
    for fp in font_paths:
        if Path(fp).exists():
            try:
                font = ImageFont.truetype(fp, WATERMARK_FONT_SIZE)
                break
            except Exception:
                continue
    if not font:
        font = ImageFont.load_default()

    # 斜对角平铺水印
    text_width = int(draw.textlength(WATERMARK_TEXT, font=font))
    text_height = WATERMARK_FONT_SIZE
    spacing_x = text_width + 100  # 水印水平间距
    spacing_y = text_height + 80  # 水印垂直间距

    for y in range(-text_height, img.size[1], spacing_y):
        for x in range(-text_width, img.size[0], spacing_x):
            draw.text((x, y), WATERMARK_TEXT, fill=(128, 128, 128, WATERMARK_OPACITY), font=font)

    # 合并水印到原图
    result = Image.alpha_composite(img, watermark_layer)

    # 转回 RGB 保存 (JPEG 不支持 RGBA)
    result.convert("RGB").save(output_path, "JPEG", quality=90)
