from hashlib import sha256
from io import BytesIO
from pathlib import Path

from fastapi import HTTPException
from PIL import Image, ImageOps, UnidentifiedImageError


SUPPORTED_FORMATS = {"PNG": "image/png", "JPEG": "image/jpeg", "WEBP": "image/webp"}


def prepare_visual_evidence(path: Path) -> tuple[bytes, str, dict]:
    try:
        with Image.open(path) as source:
            image_format = source.format
            if image_format not in SUPPORTED_FORMATS:
                raise HTTPException(status_code=415, detail="该格式暂不支持 AI 评估")
            original_width, original_height = source.size
            if original_width * original_height > 40_000_000:
                raise HTTPException(status_code=413, detail="图片像素尺寸超过处理限制")
            source.load()
            prepared = ImageOps.exif_transpose(source)
            prepared.thumbnail((2048, 2048), Image.Resampling.LANCZOS)
            if image_format == "JPEG":
                prepared = prepared.convert("RGB")
            output = BytesIO()
            save_options = {"quality": 90, "optimize": True} if image_format in {"JPEG", "WEBP"} else {"optimize": True}
            prepared.save(output, format=image_format, **save_options)
    except HTTPException:
        raise
    except (Image.DecompressionBombError, UnidentifiedImageError, OSError, ValueError):
        raise HTTPException(status_code=415, detail="作品文件不是有效图片") from None
    content = output.getvalue()
    summary = {
        "original_width": original_width,
        "original_height": original_height,
        "prepared_width": prepared.width,
        "prepared_height": prepared.height,
        "prepared_sha256": sha256(content).hexdigest(),
        "exif_removed": True,
    }
    return content, SUPPORTED_FORMATS[image_format], summary
