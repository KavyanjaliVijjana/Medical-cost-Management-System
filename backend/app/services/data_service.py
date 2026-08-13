from dataclasses import dataclass
from threading import Lock
from typing import Any

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.db.models.dataset import Dataset
from app.repositories.dataset_repository import DatasetRepository
from app.schemas.dataset import DatasetValidationResponse
from app.seed.demo_dataset import DEMO_DATASET_NAME, build_demo_dataset_csv
from app.validation.csv_validator import CsvValidationResult, validate_csv_bytes


@dataclass
class PendingDataset:
    records: list[dict[str, Any]]


class DataService:
    """Coordinates validation, staged confirmation, and canonical record persistence."""

    def __init__(self) -> None:
        self.repository = DatasetRepository()
        self._pending_datasets: dict[int, PendingDataset] = {}
        self._lock = Lock()

    async def validate_upload(self, db: Session, file: UploadFile) -> DatasetValidationResponse:
        content = await file.read()
        return self._validate_and_stage(
            db,
            content=content,
            filename=file.filename,
            content_type=file.content_type,
            dataset_name=_display_name(file.filename),
            source_type="uploaded",
            is_synthetic=False,
        )

    def validate_demo_dataset(self, db: Session) -> DatasetValidationResponse:
        return self._validate_and_stage(
            db,
            content=build_demo_dataset_csv(),
            filename="synthetic_demo_dataset.csv",
            content_type="text/csv",
            dataset_name=DEMO_DATASET_NAME,
            source_type="synthetic",
            is_synthetic=True,
        )

    def _validate_and_stage(
        self,
        db: Session,
        *,
        content: bytes,
        filename: str | None,
        content_type: str | None,
        dataset_name: str,
        source_type: str,
        is_synthetic: bool,
    ) -> DatasetValidationResponse:
        result: CsvValidationResult = validate_csv_bytes(content, filename, content_type)
        if not result.summary.is_valid:
            return DatasetValidationResponse(validation=result.summary)

        dataset = self.repository.create_dataset(
            db,
            name=dataset_name,
            source_type=source_type,
            is_synthetic=is_synthetic,
            row_count=result.summary.valid_rows,
        )
        with self._lock:
            self._pending_datasets[dataset.id] = PendingDataset(records=result.records)
        return DatasetValidationResponse(
            dataset=dataset,
            validation=result.summary,
            preview=[_serialize_preview(record) for record in result.records[:10]],
        )

    def process_dataset(self, db: Session, dataset_id: int) -> Dataset:
        dataset = self._get_dataset_or_404(db, dataset_id)
        if dataset.processing_status == "completed":
            return dataset
        with self._lock:
            pending = self._pending_datasets.get(dataset_id)
        if pending is None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="The validation session is no longer available. Please validate the CSV again before processing.",
            )
        dataset.processing_status = "processing"
        db.commit()
        try:
            self.repository.add_records(db, dataset, pending.records)
        except Exception:
            db.rollback()
            dataset = self._get_dataset_or_404(db, dataset_id)
            dataset.processing_status = "failed"
            db.commit()
            raise
        with self._lock:
            self._pending_datasets.pop(dataset_id, None)
        return dataset

    def get_dataset(self, db: Session, dataset_id: int) -> Dataset:
        return self._get_dataset_or_404(db, dataset_id)

    def get_preview(self, db: Session, dataset_id: int) -> list[Any]:
        self._get_dataset_or_404(db, dataset_id)
        return self.repository.list_records(db, dataset_id, limit=10)

    def list_completed_datasets(self, db: Session) -> list[Dataset]:
        return self.repository.list_completed_datasets(db)

    def _get_dataset_or_404(self, db: Session, dataset_id: int) -> Dataset:
        dataset = self.repository.get_dataset(db, dataset_id)
        if dataset is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found.")
        return dataset


def _display_name(filename: str | None) -> str:
    return filename.rsplit(".", 1)[0] if filename else "Uploaded dataset"


def _serialize_preview(record: dict[str, Any]) -> dict[str, Any]:
    return {key: value.isoformat() if hasattr(value, "isoformat") else value for key, value in record.items()}


data_service = DataService()
