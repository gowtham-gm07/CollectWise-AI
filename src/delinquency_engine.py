
import sqlite3
import math
from datetime import date

from src.schema import DB_PATH

REFERENCE_DATE = date(2026, 10, 22)


def calculate_priority(dpd, arrears, risk_segment, hardship_flag):
    # Higher score means greater collection priority.
    dpd_score = min(dpd / 90, 1) * 60
    arrears_score = min(arrears / 100000, 1) * 20

    risk_score = {
        "LOW": 5,
        "MEDIUM": 10,
        "HIGH": 15
    }.get(risk_segment, 5)

    hardship_adjustment = -10 if hardship_flag else 0

    return round(
        max(0, min(
            100,
            dpd_score + arrears_score +
            risk_score + hardship_adjustment
        )),
        2
    )


def run_delinquency_engine():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("PRAGMA foreign_keys = ON")

        conn.execute("DELETE FROM delinquency_snapshots")
        conn.execute("DELETE FROM collection_cases")

        loans = conn.execute("""
            SELECT
                l.loan_id,
                c.risk_segment,
                c.hardship_flag
            FROM loans l
            JOIN customers c
                ON l.customer_id = c.customer_id
            ORDER BY l.loan_id
        """).fetchall()

        case_number = 0

        for index, (loan_id, risk_segment, hardship_flag) in enumerate(
            loans, start=1
        ):
            installments = conn.execute("""
                SELECT due_date, amount_due, amount_paid
                FROM installments
                WHERE loan_id = ?
                ORDER BY due_date
            """, (loan_id,)).fetchall()

            overdue_items = []

            for due_date_text, amount_due, amount_paid in installments:
                due_date = date.fromisoformat(due_date_text)
                remaining = max(0, amount_due - amount_paid)

                if due_date < REFERENCE_DATE and remaining > 0:
                    overdue_items.append((due_date, remaining))

            if overdue_items:
                oldest_due_date = min(item[0] for item in overdue_items)
                dpd = (REFERENCE_DATE - oldest_due_date).days
                arrears = round(sum(item[1] for item in overdue_items), 2)
            else:
                dpd = 0
                arrears = 0.0

            snapshot_id = f"SNP-2026-{index:06d}"

            conn.execute("""
                INSERT INTO delinquency_snapshots
                VALUES (?, ?, ?, ?, ?)
            """, (
                snapshot_id,
                loan_id,
                REFERENCE_DATE.isoformat(),
                dpd,
                arrears
            ))

            if dpd > 0 and arrears > 0:
                case_number += 1

                case_id = f"COL-2026-{case_number:06d}"

                priority_score = calculate_priority(
                    dpd,
                    arrears,
                    risk_segment,
                    hardship_flag
                )

                conn.execute("""
                    INSERT INTO collection_cases
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    case_id,
                    loan_id,
                    dpd,
                    arrears,
                    priority_score,
                    "OPEN",
                    "DELINQUENCY"
                ))

        conn.commit()

        total_cases = conn.execute(
            "SELECT COUNT(*) FROM collection_cases"
        ).fetchone()[0]

        total_snapshots = conn.execute(
            "SELECT COUNT(*) FROM delinquency_snapshots"
        ).fetchone()[0]

        print("Delinquency engine completed.")
        print(f"Snapshots created: {total_snapshots}")
        print(f"Collection cases created: {total_cases}")


if __name__ == "__main__":
    run_delinquency_engine()
