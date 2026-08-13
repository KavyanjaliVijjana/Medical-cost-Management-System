from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.db.models.alert import Alert
from app.db.models.driver_insight import DriverInsight


class InsightRepository:
    def replace_drivers(self, db: Session, dataset_id: int, items: list[dict[str, object]]) -> list[DriverInsight]:
        db.execute(delete(DriverInsight).where(DriverInsight.dataset_id == dataset_id))
        db.add_all([DriverInsight(dataset_id=dataset_id, **item) for item in items])
        db.commit()
        return self.list_drivers(db, dataset_id)

    def list_drivers(self, db: Session, dataset_id: int) -> list[DriverInsight]:
        return list(db.scalars(select(DriverInsight).where(DriverInsight.dataset_id == dataset_id).order_by(DriverInsight.id)))

    def replace_alerts(self, db: Session, dataset_id: int, items: list[dict[str, object]]) -> list[Alert]:
        db.execute(delete(Alert).where(Alert.dataset_id == dataset_id))
        db.add_all([Alert(dataset_id=dataset_id, **item) for item in items])
        db.commit()
        return self.list_alerts(db, dataset_id)

    def list_alerts(self, db: Session, dataset_id: int) -> list[Alert]:
        return list(db.scalars(select(Alert).where(Alert.dataset_id == dataset_id, Alert.status == "active").order_by(Alert.severity.desc(), Alert.id)))
