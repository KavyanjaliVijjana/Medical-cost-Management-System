import csv
import io
from datetime import date


DEMO_DATASET_NAME = "Synthetic Demo Dataset"


def build_demo_dataset_csv() -> bytes:
    """Build a deterministic, clearly synthetic dataset for hackathon demonstrations."""
    rows: list[dict[str, object]] = []
    departments = [
        ("Cardiology", 12600, 92, 0.018),
        ("Emergency", 8800, 148, 0.010),
        ("Oncology", 16800, 58, 0.026),
        ("Orthopedics", 10400, 76, 0.014),
        ("Pharmacy", 7600, 205, 0.032),
    ]
    for month in range(1, 13):
        seasonal_factor = 1.08 if month in (1, 2, 11, 12) else 1.0
        for department, base_cost, base_patients, growth in departments:
            patients = round(base_patients * (1 + 0.006 * month))
            cost = round(base_cost * (1 + growth * month) * seasonal_factor, 2)
            rows.append(
                {
                    "date": date(2025, month, 1).isoformat(),
                    "department": department,
                    "patient_count": patients,
                    "total_cost": cost,
                }
            )

    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=["date", "department", "patient_count", "total_cost"])
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue().encode("utf-8")
