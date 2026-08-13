from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.insights import AlertResponse, DriverInsightResponse
from app.services.alert_service import alert_service
from app.services.driver_analysis_service import driver_analysis_service

router = APIRouter(prefix="/insights/datasets/{dataset_id}", tags=["insights"])


@router.post("/drivers/generate", response_model=list[DriverInsightResponse])
def generate_drivers(dataset_id: int, db: Session = Depends(get_db)):
    return driver_analysis_service.generate(db, dataset_id)


@router.get("/drivers", response_model=list[DriverInsightResponse])
def get_drivers(dataset_id: int, db: Session = Depends(get_db)):
    return driver_analysis_service.list(db, dataset_id)


@router.post("/alerts/generate", response_model=list[AlertResponse])
def generate_alerts(dataset_id: int, db: Session = Depends(get_db)):
    return alert_service.generate(db, dataset_id)


@router.get("/alerts", response_model=list[AlertResponse])
def get_alerts(dataset_id: int, db: Session = Depends(get_db)):
    return alert_service.list(db, dataset_id)
