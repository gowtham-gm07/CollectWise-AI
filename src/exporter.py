
import sqlite3
import csv
import json
from pathlib import Path

from src.schema import DB_PATH


TABLES = [
    "customers",
    "accounts",
    "loans",
    "installments",
    "contact_preferences",
    "delinquency_snapshots",
    "collection_cases",
    "contact_attempts",
    "promises_to_pay",
    "payments",
    "case_events",
    "anomaly_labels"
]


def export_data():
    export_dir = Path("exports")
    export_dir.mkdir(exist_ok=True)

    with sqlite3.connect(DB_PATH) as conn:
        for table in TABLES:

            cursor = conn.execute(f"SELECT * FROM {table}")

            columns = [
                description[0]
                for description in cursor.description
            ]

            rows = cursor.fetchall()

            # Export CSV
            csv_path = export_dir / f"{table}.csv"

            with open(
                csv_path, "w", newline="", encoding="utf-8"
            ) as file:
                writer = csv.writer(file)
                writer.writerow(columns)
                writer.writerows(rows)

            # Export JSON
            json_path = export_dir / f"{table}.json"

            records = [
                dict(zip(columns, row))
                for row in rows
            ]

            with open(
                json_path, "w", encoding="utf-8"
            ) as file:
                json.dump(
                    records,
                    file,
                    indent=4,
                    default=str
                )

            print(
                f"Exported {table}: {len(rows)} records"
            )

        # Export SQL database schema and data
        sql_path = export_dir / "collectwise_export.sql"

        with open(
            sql_path, "w", encoding="utf-8"
        ) as file:
            for line in conn.iterdump():
                file.write(line + "\n")

    print("\nAll exports completed.")
    print(f"Export directory: {export_dir.resolve()}")


if __name__ == "__main__":
    export_data()
