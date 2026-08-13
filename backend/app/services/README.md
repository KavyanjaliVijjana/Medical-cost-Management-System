# Application service boundaries

Phase 2 adds `data_service.py`; future phases add deterministic business logic here rather than embedding it in FastAPI routes.

- `data_service.py` — Phase 2 ingestion and processing.
- `analytics_service.py` — Phase 3 metrics and chronological aggregation.
- `forecast_service.py` — Phase 4 Linear Regression forecasting and chronological evaluation.
- `driver_analysis_service.py` and `alert_service.py` — Phase 5 insight detection.
- `recommendation_service.py` — Phase 6 rule-based recommendations.
- `scenario_service.py` — Phase 7 what-if calculations.
- `report_service.py` — Phase 8 report composition.

These boundaries are reserved so any later AI layer can call stable service interfaces without directly accessing the database.
