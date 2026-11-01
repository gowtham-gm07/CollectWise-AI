
import random
import sqlite3
from datetime import date, timedelta

from src.schema import DB_PATH

SEED = 20261022
REFERENCE_DATE = date(2026, 10, 22)


def run_promise_engine():
    random.seed(SEED)

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("PRAGMA foreign_keys = ON")

        conn.execute("DELETE FROM promises_to_pay")

        cases = conn.execute("""
            SELECT case_id, loan_id, arrears
            FROM collection_cases
            WHERE case_status = 'OPEN'
            ORDER BY case_id
        """).fetchall()

        promise_number = 0

        for case_id, loan_id, arrears in cases:

            # Only some customers make payment commitments
            if random.random() > 0.45:
                continue

            if arrears <= 0:
                continue

            promised_amount = round(
                arrears * random.uniform(0.20, 1.00), 2
            )

            promised_date = REFERENCE_DATE + timedelta(
                days=random.randint(-15, 15)
            )

            if promised_date > REFERENCE_DATE:
                promise_status = "PENDING"
            else:
                payments_after_promise = conn.execute("""
                    SELECT COALESCE(SUM(amount), 0)
                    FROM payments
                    WHERE loan_id = ?
                    AND payment_date >= ?
                """, (
                    loan_id,
                    promised_date.isoformat()
                )).fetchone()[0]

                promise_status = (
                    "KEPT"
                    if payments_after_promise >= promised_amount
                    else "MISSED"
                )

            promise_number += 1
            promise_id = f"PTP-2026-{promise_number:06d}"

            conn.execute("""
                INSERT INTO promises_to_pay (
                    promise_id,
                    case_id,
                    promised_amount,
                    promised_date,
                    promise_status
                )
                VALUES (?, ?, ?, ?, ?)
            """, (
                promise_id,
                case_id,
                promised_amount,
                promised_date.isoformat(),
                promise_status
            ))

        conn.commit()

        results = conn.execute("""
            SELECT promise_status, COUNT(*)
            FROM promises_to_pay
            GROUP BY promise_status
        """).fetchall()

        print("Promise-to-Pay engine completed.")
        print(f"Total promises created: {promise_number}")

        for status, count in results:
            print(f"{status}: {count}")


if __name__ == "__main__":
    run_promise_engine()
