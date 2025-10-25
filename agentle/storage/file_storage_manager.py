"""Abstract file storage manager interface."""

from abc import ABC, abstractmethod


class FileStorageManager(ABC):
    """Interface for file storage management."""

    @abstractmethod
    async def upload_file(self, file_data: bytes, filename: str, mime_type: str) -> str:
        """
        Upload file to storage and return public URL.

        Args:
            file_data: The file content as bytes
            filename: The filename to use for storage
            mime_type: The MIME type of the file

        Returns:
            Public URL to access the uploaded file

        Raises:
            FileStorageError: If upload fails
        """
        pass

    @abstractmethod
    async def delete_file(self, file_url: str) -> bool:
        """
        Delete file from storage by URL.

        Args:
            file_url: The public URL of the file to delete

        Returns:
            True if deletion was successful, False otherwise
        """
        pass


class FileStorageError(Exception):
    """Exception raised for file storage operations."""

    pass
