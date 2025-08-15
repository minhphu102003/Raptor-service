from fastapi import File, HTTPException, UploadFile, status

ALLOWED_EXTS = (".md", ".markdown")
ALLOWED_CT = {"text/markdown", "text/x-markdown", "text/plain"}


async def require_markdown_file(file: UploadFile = File(...)) -> UploadFile:
    name = (file.filename or "").lower()

    if not name.endswith(ALLOWED_EXTS):
        raise HTTPException(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Only .md or .markdown files are allowed.",
        )

    head = await file.read(4096)
    try:
        head.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="File is not valid UTF-8 text; expecting Markdown text.",
        )
    finally:
        await file.seek(0)

    return file
