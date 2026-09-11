import json
from pathlib import Path
from uuid import uuid4
from zipfile import BadZipFile, ZipFile, is_zipfile

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
    ".py": {"text/plain", "text/x-python", "application/octet-stream"},
    ".js": {"text/plain", "text/javascript", "application/javascript", "application/octet-stream"},
    ".ts": {"text/plain", "text/typescript", "application/octet-stream"},
    ".tsx": {"text/plain", "text/typescript", "application/octet-stream"},
    ".java": {"text/plain", "text/x-java-source", "application/octet-stream"},
    ".c": {"text/plain", "text/x-c", "application/octet-stream"},
    ".cpp": {"text/plain", "text/x-c++src", "application/octet-stream"},
    ".go": {"text/plain", "text/x-go", "application/octet-stream"},
    ".rs": {"text/plain", "application/octet-stream"},
    ".sql": {"text/plain", "application/sql", "application/octet-stream"},
    ".ipynb": {"application/json", "application/x-ipynb+json", "application/octet-stream"},
    ".json": {"application/json", "text/plain", "application/octet-stream"},
    ".md": {"text/markdown", "text/plain", "application/octet-stream"},
    ".txt": {"text/plain", "application/octet-stream"},
}

IMAGE_FORMATS = {
    ".png": "PNG",
    ".jpg": "JPEG",
    ".jpeg": "JPEG",
    ".webp": "WEBP",
}
UPLOAD_IMAGE_FORMATS = {**IMAGE_FORMATS, ".gif": "GIF"}
MAX_IMAGE_PIXELS = 40_000_000
SOURCE_FORMATS = {".py", ".js", ".ts", ".tsx", ".java", ".c", ".cpp", ".go", ".rs", ".sql", ".ipynb", ".json", ".md", ".txt"}


def _invalid_file() -> HTTPException:
    return HTTPException(status_code=415, detail="文件内容与声明格式不一致")


def _validate_saved_file(destination: Path, extension: str) -> None:
    header = destination.read_bytes()[:16]
    if extension in UPLOAD_IMAGE_FORMATS:
        try:
            with Image.open(destination) as image:
                if image.width * image.height > MAX_IMAGE_PIXELS:
                    raise HTTPException(status_code=413, detail="图片像素尺寸超过处理限制")
                image.verify()
                if image.format != UPLOAD_IMAGE_FORMATS[extension]:
                    raise _invalid_file()
        except HTTPException:
            raise
        except (Image.DecompressionBombError, UnidentifiedImageError, OSError, ValueError):
            raise HTTPException(status_code=415, detail="文件内容不是有效图片") from None
        return
    if extension in SOURCE_FORMATS:
        content = destination.read_bytes()
        if b"\x00" in content:
            raise _invalid_file()
        try:
            decoded = content.decode("utf-8")
        except UnicodeDecodeError:
            raise HTTPException(status_code=415, detail="代码和文本文件必须使用 UTF-8 编码") from None
        if extension in {".json", ".ipynb"}:
            try:
                json.loads(decoded)
            except json.JSONDecodeError:
                raise _invalid_file() from None
        return
    if extension == ".pdf" and not header.startswith(b"%PDF-"):
        raise _invalid_file()
    if extension == ".doc" and not header.startswith(b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"):
        raise _invalid_file()
    if extension in {".docx", ".pptx"}:
        if not is_zipfile(destination):
            raise _invalid_file()
        try:
            with ZipFile(destination) as archive:
                names = set(archive.namelist())
        except (BadZipFile, OSError):
            raise _invalid_file() from None
        required_prefix = "word/" if extension == ".docx" else "ppt/"
        if "[Content_Types].xml" not in names or not any(
            name.startswith(required_prefix) for name in names
        ):
            raise _invalid_file()
    if extension == ".mp4" and not (len(header) >= 12 and header[4:8] == b"ftyp"):
        raise _invalid_file()
    if extension == ".webm" and not header.startswith(b"\x1aE\xdf\xa3"):
        raise _invalid_file()


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
        _validate_saved_file(destination, extension)
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
