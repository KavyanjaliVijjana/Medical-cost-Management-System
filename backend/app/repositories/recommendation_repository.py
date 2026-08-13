import json

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.db.models.recommendation import Recommendation


class RecommendationRepository:
    def replace(self, db: Session, dataset_id: int, items: list[dict[str, object]]) -> list[Recommendation]:
        db.execute(delete(Recommendation).where(Recommendation.dataset_id == dataset_id))
        db.add_all([Recommendation(dataset_id=dataset_id, **item) for item in items])
        db.commit()
        return self.list(db, dataset_id)

    def list(self, db: Session, dataset_id: int) -> list[Recommendation]:
        return list(db.scalars(select(Recommendation).where(Recommendation.dataset_id == dataset_id).order_by(Recommendation.id)))


def evidence_json(items: list[str]) -> str:
    return json.dumps(items)


def parse_evidence(value: str) -> list[str]:
    return json.loads(value)
