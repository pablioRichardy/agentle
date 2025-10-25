"""Local file storage manager implementation."""

import logging
import os
import time
from pathlib import Path
from typing import Any

from agentle.storage.file_storage_manager import FileStorageError, FileStorageManager

logger = logging.getLogger(__name__)


class LocalFileStorageManager(FileStorageManager):
    """Local filesystem implementation of file storage manager."""

    def __init__(
        self,
        storage_dir: str | Path = "./storage",
        base_url: str = "http://localhost:8000",
        create_dirs: bool = True,
    ):
        """
        Initialize local file storage manager.

        Args:
            storage_dir: Directory to store files
            base_url: Base URL for accessing files (e.g., "http://localhost:8000")
            create_dirs: Whether to create storage directory if it doesn't exist
        """
        self.storage_dir = Path(storage_dir)
        self.base_url = base_url.rstrip("/")

        if create_dirs:
            self.storage_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created storage directory: {self.storage_dir}")

        logger.info(f"LocalFileStorageManager initialized: {self.storage_dir}")

    async def upload_file(self, file_data: bytes, filename: str, mime_type: str) -> str:
        """Upload file to local storage and return public URL."""
        try:
            # Ensure filename is safe
            safe_filename = self._make_filename_safe(filename)
            file_path = self.storage_dir / safe_filename

            logger.debug(
                f"Uploading file to local storage: {file_path} ({len(file_data)} bytes)"
            )

            # Write file to disk
            with open(file_path, "wb") as f:
                f.write(file_data)

            # Generate public URL
            url = f"{self.base_url}/files/{safe_filename}"

            logger.info(f"File uploaded successfully: {url}")
            return url

        except OSError as e:
            error_msg = f"Failed to write file to local storage: {e}"
            logger.error(error_msg)
            raise FileStorageError(error_msg) from e
        except Exception as e:
            error_msg = f"Unexpected error uploading to local storage: {e}"
            logger.error(error_msg)
            raise FileStorageError(error_msg) from e

    async def delete_file(self, file_url: str) -> bool:
        """Delete file from local storage by URL."""
        try:
            # Extract filename from URL
            if "/files/" in file_url:
                filename = file_url.split("/files/")[-1]
            else:
                logger.warning(f"Could not extract filename from URL: {file_url}")
                return False

            file_path = self.storage_dir / filename

            if not file_path.exists():
                logger.warning(f"File not found: {file_path}")
                return False

            logger.debug(f"Deleting file from local storage: {file_path}")

            file_path.unlink()

            logger.info(f"File deleted successfully: {filename}")
            return True

        except OSError as e:
            logger.error(f"Failed to delete file from local storage: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error deleting from local storage: {e}")
            return False

    def _make_filename_safe(self, filename: str) -> str:
        """Make filename safe for filesystem."""
        # Remove or replace unsafe characters
        safe_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.-_"
        safe_filename = "".join(c if c in safe_chars else "_" for c in filename)

        # Ensure it's not empty and has reasonable length
        if not safe_filename or len(safe_filename) > 255:
            timestamp = int(time.time())
            safe_filename = f"file_{timestamp}"

        return safe_filename

    def get_storage_info(self) -> dict[str, Any]:
        """Get information about the storage configuration."""
        return {
            "storage_dir": str(self.storage_dir),
            "base_url": self.base_url,
            "exists": self.storage_dir.exists(),
            "is_writable": os.access(self.storage_dir, os.W_OK)
            if self.storage_dir.exists()
            else False,
        }
