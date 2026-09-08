"""Filesystem utilities."""

import shutil
from pathlib import Path

from toolkit.config.constants import (
    DEFAULT_CONFIG,
    FILE_PATTERNS,
    MESSAGES,
)
from toolkit.core.logging import logger


def ensure_directory(path: Path) -> Path:
    """Ensure directory exists, create if not."""
    path.mkdir(parents=True, exist_ok=True)
    return path


def backup_file(file_path: Path) -> Path | None:
    """Create a backup of a file."""
    if not file_path.exists():
        logger.warning(MESSAGES.WARNING_FILE_NOT_FOUND.format(file_path))
        return None

    from datetime import datetime

    timestamp = datetime.now().strftime(DEFAULT_CONFIG.BACKUP_TIMESTAMP_FORMAT)
    backup_path = file_path.parent / f"{file_path.name}.{timestamp}{FILE_PATTERNS.BACKUP_SUFFIX}"

    try:
        shutil.copy2(file_path, backup_path)
        logger.success(MESSAGES.SUCCESS_BACKUP_CREATED.format(backup_path))
        return backup_path
    except Exception as e:
        logger.error(MESSAGES.ERROR_FAILED_BACKUP.format(file_path, e))
        return None
