from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile
from PIL import Image, UnidentifiedImageError


ALLOWED_TYPES = {
    ".png": {"image/png"},
    ".jpg": {"image/jpeg"},
    ".jpeg": {"image/jpeg"},
    ".gif": {"image/gif"},
    ".webp": {"image/webp"},
    ".mp4": {"video/mp4"},
    ".webm": {"video/webm"},
    ".pdf": {"application/pdf"},
    ".doc": {"application/msword"},
    ".docx": {"application/vnd.openxmlformats-officedocument.wordprocessingml.document"},
    ".ppt": {"application/vnd.ms-powerpoint"},
    ".pptx": {"application/vnd.openxmlformats-officedocument.presentationml.presentation"},
}

IMAGE_FORMATS = {
    ".png": "PNG",
    ".jpg": "JPEG",
    ".jpeg": "JPEG",
    ".webp": "WEBP",
}


async def save_upload(file: UploadFile, upload_dir: Path, max_bytes: int) -> str:
    extension = Path(file.filename or "").suffix.lower()
    if extension not in ALLOWED_TYPES or file.content_type not in ALLOWED_TYPES[extension]:
        raise HTTPException(status_code=415, detail="不支持的文件类型")

    upload_dir.mkdir(parents=True, exist_ok=True)
    stored_name = f"{uuid4().hex}{extension}"
    destination = upload_dir / stored_name
    total = 0
    try:
        with destination.open("wb") as output:
            while chunk := await file.read(64 * 1024):
                total += len(chunk)
                if total > max_bytes:
                    raise HTTPException(status_code=413, detail="文件超过大小限制")
                output.write(chunk)
        if extension in IMAGE_FORMATS:
            try:
                with Image.open(destination) as image:
                    image.verify()
                    if image.format != IMAGE_FORMATS[extension]:
                        raise HTTPException(
                            status_code=415, detail="图片扩展名与真实格式不一致"
                        )
            except UnidentifiedImageError:
                raise HTTPException(
                    status_code=415, detail="文件内容不是有效图片"
                ) from None
            except (OSError, ValueError):
                raise HTTPException(
                    status_code=415, detail="文件内容不是有效图片"
                ) from None
    except BaseException:
        destination.unlink(missing_ok=True)
        raise
    finally:
        await file.close()
    return stored_name


def upload_path(upload_dir: Path, file_url: str) -> Path:
    stored_name = Path(file_url).name
    candidate = (upload_dir / stored_name).resolve()
    root = upload_dir.resolve()
    if candidate.parent != root:
        raise HTTPException(status_code=404, detail="作品文件不存在")
    return candidate


def remove_upload(upload_dir: Path, file_url: str) -> None:
    candidate = upload_path(upload_dir, file_url)
    candidate.unlink(missing_ok=True)
