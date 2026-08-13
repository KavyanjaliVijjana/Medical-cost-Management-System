from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.cost_record import CostRecord
from app.db.models.dataset import Dataset


class DatasetRepository:
    """Persistence operations for Phase 2 dataset ingestion."""

    def create_dataset(
        self, db: Session, *, name: str, source_type: str, is_synthetic: bool, row_count: int
    ) -> Dataset:
        dataset = Dataset(
            name=name,
            source_type=source_type,
            is_synthetic=is_synthetic,
            row_count=row_count,
            processing_status="ready",
        )
        db.add(dataset)
        db.commit()
        db.refresh(dataset)
        return dataset

    def get_dataset(self, db: Session, dataset_id: int) -> Dataset | None:
        return db.get(Dataset, dataset_id)

    def add_records(self, db: Session, dataset: Dataset, records: list[dict[str, object]]) -> None:
        db.add_all([CostRecord(dataset_id=dataset.id, **record) for record in records])
        dataset.processing_status = "completed"
        db.commit()
        db.refresh(dataset)

    def list_records(self, db: Session, dataset_id: int, limit: int) -> list[CostRecord]:
        statement = (
            select(CostRecord)
            .where(CostRecord.dataset_id == dataset_id)
            .order_by(CostRecord.record_date, CostRecord.id)
            .limit(limit)
        )
        return list(db.scalars(statement))

    def list_all_records(self, db: Session, dataset_id: int) -> list[CostRecord]:
        statement = (
            select(CostRecord)
            .where(CostRecord.dataset_id == dataset_id)
            .order_by(CostRecord.record_date, CostRecord.id)
        )
        return list(db.scalars(statement))

    def list_completed_datasets(self, db: Session) -> list[Dataset]:
        statement = (
            select(Dataset)
            .where(Dataset.processing_status == "completed")
            .order_by(Dataset.uploaded_at.desc(), Dataset.id.desc())
        )
        return list(db.scalars(statement))
