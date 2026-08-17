import csv
import random
from datetime import date, timedelta
from pathlib import Path


OUTPUT_DIR = Path(__file__).parent

DEPARTMENTS = [
    ("Cardiology", 12600, 92, 0.018),
    ("Emergency", 8800, 148, 0.010),
    ("Oncology", 16800, 58, 0.026),
    ("Orthopedics", 10400, 76, 0.014),
    ("Pharmacy", 7600, 205, 0.032),
]

FIELDS = [
    "date",
    "department",
    "patient_count",
    "total_cost",
]


def generate_dataset(target_rows: int, filename: str, seed: int = 42) -> None:
    random.seed(seed)

    rows = []

    for index in range(target_rows):
        department, base_cost, base_patients, growth = DEPARTMENTS[
            index % len(DEPARTMENTS)
        ]

        month_index = index % 12
        month = month_index + 1

        seasonal_factor = (
            1.08 if month in (1, 2, 11, 12) else 1.0
        )

        patients = round(
            base_patients
            * (1 + 0.006 * month)
            * random.uniform(0.90, 1.10)
        )

        cost = (
            base_cost
            * (1 + growth * month)
            * seasonal_factor
            * random.uniform(0.95, 1.05)
        )

        # Small deterministic offset guarantees that complete
        # rows cannot accidentally become identical after rounding.
        cost += index * 0.01

        # Spread records across a multi-year period.
        record_date = date(2023, 1, 1) + timedelta(days=index)

        rows.append(
            {
                "date": record_date.isoformat(),
                "department": department,
                "patient_count": max(1, patients),
                "total_cost": round(cost, 2),
            }
        )

    output_path = OUTPUT_DIR / filename

    with output_path.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=FIELDS,
        )

        writer.writeheader()
        writer.writerows(rows)

    print(
        f"Created {output_path.name}: "
        f"{len(rows):,} rows"
    )


if __name__ == "__main__":
    generate_dataset(10_000, "medical_cost_10k.csv")
    generate_dataset(25_000, "medical_cost_25k.csv")
    generate_dataset(50_000, "medical_cost_50k.csv")
    generate_dataset(100_000, "medical_cost_100k.csv")
    generate_dataset(250_000, "medical_cost_250k.csv")