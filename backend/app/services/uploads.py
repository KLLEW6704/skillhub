from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile


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
    except BaseException:
        destination.unlink(missing_ok=True)
        raise
    finally:
        await file.close()
    return stored_name


def remove_upload(upload_dir: Path, file_url: str) -> None:
    stored_name = Path(file_url).name
    candidate = (upload_dir / stored_name).resolve()
    root = upload_dir.resolve()
    if candidate.parent == root:
        candidate.unlink(missing_ok=True)
