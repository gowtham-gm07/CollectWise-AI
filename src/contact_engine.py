
import random
import sqlite3
from datetime import date, datetime, timedelta

from src.schema import DB_PATH

SEED = 20261022
REFERENCE_DATE = date(2026, 10, 22)


def run_contact_engine():
    random.seed(SEED)

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("DELETE FROM contact_attempts")

        cases = conn.execute("""
            SELECT
                cc.case_id,
                c.customer_id,
                cp.preferred_channel,
                cp.contact_start,
                cp.contact_end,
                cp.do_not_contact
            FROM collection_cases cc
            JOIN loans l ON cc.loan_id = l.loan_id
            JOIN customers c ON l.customer_id = c.customer_id
            JOIN contact_preferences cp
                ON c.customer_id = cp.customer_id
            WHERE cc.case_status = 'OPEN'
            ORDER BY cc.case_id
        """).fetchall()

        attempt_number = 0
        skipped_dnc = 0

        for (
            case_id,
            customer_id,
            channel,
            contact_start,
            contact_end,
            do_not_contact
        ) in cases:

            # Respect customer contact restrictions
            if do_not_contact:
                skipped_dnc += 1
                continue

            # Generate a simulated contact date within the last 7 days
            contact_date = REFERENCE_DATE - timedelta(
                days=random.randint(0, 6)
            )

            start_hour, start_minute = map(
                int, contact_start.split(":")
            )

            end_hour, end_minute = map(
                int, contact_end.split(":")
            )

            start_minutes = start_hour * 60 + start_minute
            end_minutes = end_hour * 60 + end_minute

            if end_minutes <= start_minutes:
                continue

            # Select a time inside the allowed contact window
            contact_minutes = random.randint(
                start_minutes, end_minutes - 1
            )

            attempted_at = datetime.combine(
                contact_date,
                datetime.min.time()
            ) + timedelta(minutes=contact_minutes)

            outcome = random.choice([
                "CONNECTED",
                "NO_ANSWER",
                "CALLBACK_REQUESTED",
                "CUSTOMER_UNAVAILABLE"
            ])

            attempt_number += 1
            attempt_id = f"CAT-2026-{attempt_number:06d}"

            conn.execute("""
                INSERT INTO contact_attempts (
                    attempt_id,
                    case_id,
                    attempted_at,
                    channel,
                    outcome,
                    compliance_status
                )
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                attempt_id,
                case_id,
                attempted_at.isoformat(timespec="minutes"),
                channel,
                outcome,
                "COMPLIANT"
            ))

        conn.commit()

        total = conn.execute(
            "SELECT COUNT(*) FROM contact_attempts"
        ).fetchone()[0]

        print("Contact management engine completed.")
        print(f"Contact attempts created: {total}")
        print(f"Do Not Contact cases skipped: {skipped_dnc}")


if __name__ == "__main__":
    run_contact_engine()
