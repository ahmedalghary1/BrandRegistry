from __future__ import annotations

import json
import shutil
import sqlite3
import tempfile
import zipfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable


SQLITE_SIGNATURE = b"SQLite format 3\x00"
ZIP_SIGNATURE = b"PK\x03\x04"
BACKUP_ARCHIVE_SUFFIX = ".backup.zip"
DATABASE_ARCHIVE_MEMBER = "database/db.sqlite3"
MEDIA_ARCHIVE_ROOT = "media/"
MANIFEST_ARCHIVE_MEMBER = "manifest.json"


class BackupOperationError(Exception):
    """Raised when a backup or restore operation cannot be completed safely."""


@dataclass(frozen=True)
class BackupRecord:
    name: str
    path: Path
    created_at: datetime
    size_bytes: int


class DatabaseBackupService:
    """Create and restore SQLite backups using SQLite's native backup API."""

    def __init__(
        self,
        database_path: Path,
        backup_dir: Path,
        media_root: Path | None = None,
        close_connections: Callable[[], None] | None = None,
        after_restore: Callable[[], None] | None = None,
        filename_prefix: str = "brandregistry-backup",
    ):
        self.database_path = Path(database_path)
        self.backup_dir = Path(backup_dir)
        self.media_root = Path(media_root) if media_root else None
        self.close_connections = close_connections
        self.after_restore = after_restore
        self.filename_prefix = filename_prefix

    def create_backup(self, backup_dir: str | Path | None = None) -> BackupRecord:
        try:
            self._ensure_sqlite_database()
            target_dir = Path(backup_dir) if backup_dir else self.backup_dir
            target_dir.mkdir(parents=True, exist_ok=True)
            backup_path = self._build_backup_path(target_dir)

            self._before_file_operation()
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_db_path = Path(temp_dir) / "db.sqlite3"
                self._backup_sqlite_file(self.database_path, temp_db_path)
                self._create_backup_archive(backup_path, temp_db_path)
            return self.describe_backup(backup_path)
        except BackupOperationError:
            raise
        except OSError as exc:
            raise BackupOperationError("تعذر الوصول إلى مجلد النسخ الاحتياطية أو الكتابة بداخله.") from exc

    def restore_from_backup(self, backup_path: str | Path) -> None:
        try:
            source_path = Path(backup_path)
            if not source_path.exists():
                raise BackupOperationError("ملف النسخة الاحتياطية غير موجود.")

            self._ensure_sqlite_database()
            self._before_file_operation()

            if self._is_backup_archive(source_path):
                self._restore_from_archive(source_path)
            else:
                self._validate_sqlite_file(source_path)
                self._backup_sqlite_file(source_path, self.database_path)

            if self.after_restore:
                self.after_restore()
        except BackupOperationError:
            raise
        except OSError as exc:
            raise BackupOperationError("تعذر قراءة ملف النسخة الاحتياطية أو الكتابة إلى قاعدة البيانات.") from exc
        except Exception as exc:
            raise BackupOperationError("تم استرجاع الملف لكن تعذر تهيئة قاعدة البيانات بعد الاستعادة.") from exc

    def list_backups(self, limit: int = 10) -> list[BackupRecord]:
        if not self.backup_dir.exists():
            return []

        backups = []
        for pattern in ("*.backup.zip", "*.sqlite3"):
            for file_path in self.backup_dir.glob(pattern):
                if not file_path.is_file():
                    continue
                backups.append(self.describe_backup(file_path))

        backups.sort(key=lambda item: item.created_at, reverse=True)
        return backups[:limit]

    def describe_backup(self, backup_path: str | Path) -> BackupRecord:
        file_path = Path(backup_path)
        stats = file_path.stat()
        return BackupRecord(
            name=file_path.name,
            path=file_path,
            created_at=datetime.fromtimestamp(stats.st_mtime),
            size_bytes=stats.st_size,
        )

    def resolve_backup_path(self, backup_name: str) -> Path:
        normalized_name = Path(backup_name).name
        resolved_path = (self.backup_dir / normalized_name).resolve()
        backup_root = self.backup_dir.resolve()

        if backup_root not in resolved_path.parents and resolved_path != backup_root:
            raise BackupOperationError("اسم ملف النسخة الاحتياطية غير صالح.")

        if not resolved_path.exists() or not resolved_path.is_file():
            raise BackupOperationError("تعذر العثور على ملف النسخة الاحتياطية المطلوب.")

        return resolved_path

    def _before_file_operation(self) -> None:
        if self.close_connections:
            self.close_connections()

    def _build_backup_path(self, backup_dir: Path) -> Path:
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        file_path = backup_dir / f"{self.filename_prefix}-{timestamp}{BACKUP_ARCHIVE_SUFFIX}"
        counter = 1

        while file_path.exists():
            file_path = backup_dir / f"{self.filename_prefix}-{timestamp}-{counter}{BACKUP_ARCHIVE_SUFFIX}"
            counter += 1

        return file_path

    def _ensure_sqlite_database(self) -> None:
        if not self.database_path.exists():
            raise BackupOperationError("قاعدة البيانات الحالية غير موجودة، تعذر تنفيذ العملية.")

    def _validate_sqlite_file(self, file_path: Path) -> None:
        with file_path.open("rb") as file_handle:
            header = file_handle.read(len(SQLITE_SIGNATURE))

        if header != SQLITE_SIGNATURE:
            raise BackupOperationError("الملف المحدد ليس نسخة SQLite احتياطية صالحة.")

        connection = None
        try:
            connection = sqlite3.connect(file_path)
            result = connection.execute("PRAGMA integrity_check;").fetchone()
        except sqlite3.Error as exc:
            raise BackupOperationError("تعذر قراءة ملف النسخة الاحتياطية المحدد.") from exc
        finally:
            if connection is not None:
                connection.close()

        if not result or result[0] != "ok":
            raise BackupOperationError("ملف النسخة الاحتياطية تالف أو غير مكتمل.")

    def _validate_backup_archive(self, file_path: Path) -> None:
        try:
            with zipfile.ZipFile(file_path, "r") as archive:
                members = set(archive.namelist())
                if DATABASE_ARCHIVE_MEMBER not in members:
                    raise BackupOperationError("ملف النسخة الاحتياطية لا يحتوي على قاعدة البيانات المطلوبة.")

                manifest_data = {}
                if MANIFEST_ARCHIVE_MEMBER in members:
                    with archive.open(MANIFEST_ARCHIVE_MEMBER) as manifest_file:
                        manifest_data = json.loads(manifest_file.read().decode("utf-8"))

                if manifest_data.get("format") not in (None, "brandregistry-backup"):
                    raise BackupOperationError("تنسيق ملف النسخة الاحتياطية غير مدعوم.")
        except BackupOperationError:
            raise
        except (OSError, zipfile.BadZipFile, json.JSONDecodeError) as exc:
            raise BackupOperationError("ملف النسخة الاحتياطية المضغوط غير صالح أو تالف.") from exc

    def _create_backup_archive(self, backup_path: Path, temp_db_path: Path) -> None:
        media_root = self.media_root
        manifest = {
            "format": "brandregistry-backup",
            "version": 2,
            "createdAt": datetime.now().isoformat(),
            "databaseFile": DATABASE_ARCHIVE_MEMBER,
            "includesMedia": bool(media_root),
        }

        with zipfile.ZipFile(backup_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.write(temp_db_path, DATABASE_ARCHIVE_MEMBER)
            archive.writestr(MANIFEST_ARCHIVE_MEMBER, json.dumps(manifest, ensure_ascii=False, indent=2))
            self._write_media_to_archive(archive, media_root)

    def _write_media_to_archive(self, archive: zipfile.ZipFile, media_root: Path | None) -> None:
        if not media_root:
            return

        media_root.mkdir(parents=True, exist_ok=True)
        archive.writestr(MEDIA_ARCHIVE_ROOT, "")

        for file_path in media_root.rglob("*"):
            if not file_path.is_file():
                continue

            relative_path = file_path.relative_to(media_root).as_posix()
            archive.write(file_path, f"{MEDIA_ARCHIVE_ROOT}{relative_path}")

    def _restore_from_archive(self, source_path: Path) -> None:
        self._validate_backup_archive(source_path)

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            with zipfile.ZipFile(source_path, "r") as archive:
                archive.extractall(temp_root)

            extracted_db_path = temp_root / DATABASE_ARCHIVE_MEMBER
            self._validate_sqlite_file(extracted_db_path)
            self._backup_sqlite_file(extracted_db_path, self.database_path)

            if self.media_root:
                extracted_media_root = temp_root / MEDIA_ARCHIVE_ROOT
                if extracted_media_root.exists():
                    self._replace_media_directory(extracted_media_root)

    def _replace_media_directory(self, source_media_root: Path) -> None:
        if not self.media_root:
            return

        if self.media_root.exists():
            shutil.rmtree(self.media_root)

        shutil.copytree(source_media_root, self.media_root)

    def _is_backup_archive(self, file_path: Path) -> bool:
        with file_path.open("rb") as file_handle:
            header = file_handle.read(len(ZIP_SIGNATURE))

        return header == ZIP_SIGNATURE

    def _backup_sqlite_file(self, source_path: Path, destination_path: Path) -> None:
        destination_path.parent.mkdir(parents=True, exist_ok=True)
        source_connection = None
        destination_connection = None

        try:
            source_connection = sqlite3.connect(source_path)
            destination_connection = sqlite3.connect(destination_path)
            source_connection.execute("PRAGMA busy_timeout = 5000;")
            source_connection.execute("PRAGMA wal_checkpoint(TRUNCATE);")
            source_connection.backup(destination_connection)
            destination_connection.commit()
        except sqlite3.Error as exc:
            raise BackupOperationError("حدث خطأ أثناء تنفيذ عملية النسخ الاحتياطي أو الاستعادة.") from exc
        finally:
            if destination_connection is not None:
                destination_connection.close()
            if source_connection is not None:
                source_connection.close()
