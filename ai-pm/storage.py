from abc import ABC, abstractmethod
import os
import uuid
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


class DbFileStorage(FileStorage):
    """Stores file contents as rows in the SQL database (STORAGE_BACKEND=db).

    Lets the hosted app persist uploads without any object-storage service —
    everything lives in the same Postgres/SQLite database as the metadata, so a
    single connection string is all the deployment needs. Suitable for the
    small files this app handles (transcripts, decks, screenshots).

    The returned path is a synthetic key ("{project_id}/{uuid}_{filename}"), not
    a filesystem path, so it is portable across hosts. Older rows that still
    hold real local filesystem paths are handled by LocalFileStorage; this class
    only ever sees keys it minted itself."""

    def save(self, project_id: str, filename: str, content: bytes | str) -> str:
        from database import SessionLocal
        from models import FileBlob

        if isinstance(content, str):
            content = content.encode("utf-8")
        path = f"{project_id}/{uuid.uuid4().hex}_{filename}"

        db = SessionLocal()
        try:
            db.add(FileBlob(path=path, project_id=project_id, content=content))
            db.commit()
        finally:
            db.close()
        return path

    def read(self, path: str) -> str:
        return self.read_bytes(path).decode("utf-8")

    def read_bytes(self, path: str) -> bytes:
        from database import SessionLocal
        from models import FileBlob

        db = SessionLocal()
        try:
            blob = db.query(FileBlob).filter_by(path=path).first()
            if blob is None:
                raise FileNotFoundError(f"No stored file for path: {path}")
            return blob.content
        finally:
            db.close()

    def delete(self, path: str) -> None:
        from database import SessionLocal
        from models import FileBlob

        db = SessionLocal()
        try:
            db.query(FileBlob).filter_by(path=path).delete(synchronize_session=False)
            db.commit()
        finally:
            db.close()


class S3FileStorage(FileStorage):
    """V2 stub. Swap STORAGE_BACKEND=s3 to activate."""
    def save(self, *args, **kwargs): raise NotImplementedError("S3 storage not implemented in v1")
    def read(self, *args, **kwargs): raise NotImplementedError("S3 storage not implemented in v1")
    def read_bytes(self, *args, **kwargs): raise NotImplementedError("S3 storage not implemented in v1")
    def delete(self, *args, **kwargs): raise NotImplementedError("S3 storage not implemented in v1")


def get_storage() -> FileStorage:
    if config.storage_backend == "local":
        return LocalFileStorage()
    elif config.storage_backend == "db":
        return DbFileStorage()
    elif config.storage_backend == "s3":
        return S3FileStorage()
    raise ValueError(f"Unknown STORAGE_BACKEND: {config.storage_backend}")
