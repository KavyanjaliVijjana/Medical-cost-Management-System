from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.dataset import DatasetPreviewResponse, DatasetResponse, DatasetValidationResponse
from app.services.data_service import data_service

router = APIRouter(prefix="/datasets", tags=["datasets"])


@router.get("", response_model=list[DatasetResponse])
def list_completed_datasets(db: Session = Depends(get_db)) -> list[DatasetResponse]:
    return data_service.list_completed_datasets(db)


@router.post("/validate", response_model=DatasetValidationResponse)
async def validate_dataset(file: UploadFile = File(...), db: Session = Depends(get_db)) -> DatasetValidationResponse:
    return await data_service.validate_upload(db, file)


@router.post("/demo/validate", response_model=DatasetValidationResponse)
def validate_demo_dataset(db: Session = Depends(get_db)) -> DatasetValidationResponse:
    return data_service.validate_demo_dataset(db)


@router.post("/{dataset_id}/process", response_model=DatasetResponse)
def process_dataset(dataset_id: int, db: Session = Depends(get_db)) -> DatasetResponse:
    return data_service.process_dataset(db, dataset_id)


@router.get("/{dataset_id}", response_model=DatasetResponse)
def get_dataset(dataset_id: int, db: Session = Depends(get_db)) -> DatasetResponse:
    return data_service.get_dataset(db, dataset_id)


@router.get("/{dataset_id}/preview", response_model=DatasetPreviewResponse)
def get_dataset_preview(dataset_id: int, db: Session = Depends(get_db)) -> DatasetPreviewResponse:
    dataset = data_service.get_dataset(db, dataset_id)
    return DatasetPreviewResponse(dataset=dataset, records=data_service.get_preview(db, dataset_id))
