import os
import uuid
import aiofiles
import logging

from app.config.settings import settings

logger = logging.getLogger(f"app.{__name__}")

async def save_document_version_file(file):
    try:
        file_id = str(uuid.uuid4())
        extension = os.path.splitext(file.filename)[1]
        save_path = os.path.join(settings.files_storage_path, f"{file_id}{extension}")

        async with aiofiles.open(save_path, "wb") as buffer:
            while chunk := await file.read(1024 * 1024):
                await buffer.write(chunk)

        logger.info(f"Document version file {file.filename} saved to {save_path}")
        return save_path
    except Exception as e:
        logger.error(f"Error saving document version file {file.filename}")
        logger.exception(e)
        raise