from abc import ABC, abstractmethod
import os
from config import config


class FileStorage(ABC):
    @abstractmethod
    def save(self, project_id: str, filename: str, content: bytes | str) -> str:
        """Save file, return the storage path (relative)."""

    @abstractmethod
    def read(self, path: str) -> str:
        """Read file contents as string."""

    @abstractmethod
    def read_bytes(self, path: str) -> bytes:
        """Read file contents as bytes."""

    @abstractmethod
    def delete(self, path: str) -> None:
        """Delete file at path."""


class LocalFileStorage(FileStorage):
    def __init__(self):
        self.base_path = config.storage_local_path

    def save(self, project_id: str, filename: str, content: bytes | str) -> str:
        dir_path = os.path.join(self.base_path, project_id)
        os.makedirs(dir_path, exist_ok=True)
        path = os.path.join(dir_path, filename)
        mode = "wb" if isinstance(content, bytes) else "w"
        with open(path, mode, encoding=None if isinstance(content, bytes) else "utf-8") as f:
            f.write(content)
        return path

    def read(self, path: str) -> str:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    def read_bytes(self, path: str) -> bytes:
        with open(path, "rb") as f:
            return f.read()

    def delete(self, path: str) -> None:
        if os.path.exists(path):
            os.remove(path)


class S3FileStorage(FileStorage):
    """V2 stub. Swap STORAGE_BACKEND=s3 to activate."""
    def save(self, *args, **kwargs): raise NotImplementedError("S3 storage not implemented in v1")
    def read(self, *args, **kwargs): raise NotImplementedError("S3 storage not implemented in v1")
    def read_bytes(self, *args, **kwargs): raise NotImplementedError("S3 storage not implemented in v1")
    def delete(self, *args, **kwargs): raise NotImplementedError("S3 storage not implemented in v1")


def get_storage() -> FileStorage:
    if config.storage_backend == "local":
        return LocalFileStorage()
    elif config.storage_backend == "s3":
        return S3FileStorage()
    raise ValueError(f"Unknown STORAGE_BACKEND: {config.storage_backend}")
