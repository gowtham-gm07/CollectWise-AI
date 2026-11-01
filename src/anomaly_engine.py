
import sqlite3

from src.schema import DB_PATH


def run_anomaly_engine():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("PRAGMA foreign_keys = ON")

        # Keep a separate record of intentionally injected anomalies
        conn.execute("""
            CREATE TABLE IF NOT EXISTS anomaly_labels (
                anomaly_id TEXT PRIMARY KEY,
                entity_name TEXT NOT NULL,
                record_id TEXT NOT NULL,
                anomaly_type TEXT NOT NULL,
                description TEXT NOT NULL
            )
        """)

        conn.execute("DELETE FROM anomaly_labels")

        def label(anomaly_id, entity, record_id, anomaly_type, description):
            conn.execute("""
                INSERT INTO anomaly_labels
                VALUES (?, ?, ?, ?, ?)
            """, (
                anomaly_id,
                entity,
                record_id,
                anomaly_type,
                description
            ))

        # 1. Paid-off loan still has an open collection case
        paid_case = conn.execute("""
            SELECT case_id, loan_id
            FROM collection_cases
            WHERE case_status = 'OPEN'
            LIMIT 1
        """).fetchone()

        if paid_case:
            case_id, loan_id = paid_case

            conn.execute("""
                UPDATE loans
                SET outstanding_balance = 0
                WHERE loan_id = ?
            """, (loan_id,))

            label(
                "ANOM-001", "collection_cases", case_id,
                "PAID_ACCOUNT_IN_COLLECTIONS",
                "Loan balance is zero but collection case remains open."
            )

        # 2. Contact attempt outside permitted contact hours
        contact = conn.execute("""
            SELECT attempt_id
            FROM contact_attempts
            LIMIT 1
        """).fetchone()

        if contact:
            attempt_id = contact[0]

            conn.execute("""
                UPDATE contact_attempts
                SET attempted_at = substr(attempted_at, 1, 10) || 'T02:00'
                WHERE attempt_id = ?
            """, (attempt_id,))

            label(
                "ANOM-002", "contact_attempts", attempt_id,
                "CONTACT_OUTSIDE_ALLOWED_WINDOW",
                "Contact attempt was moved to 02:00."
            )

        # 3. Payment allocated to another loan's installment
        payment = conn.execute("""
            SELECT payment_id, loan_id
            FROM payments
            LIMIT 1
        """).fetchone()

        if payment:
            payment_id, payment_loan_id = payment

            wrong_installment = conn.execute("""
                SELECT installment_id
                FROM installments
                WHERE loan_id != ?
                LIMIT 1
            """, (payment_loan_id,)).fetchone()

            if wrong_installment:
                conn.execute("""
                    UPDATE payments
                    SET installment_id = ?
                    WHERE payment_id = ?
                """, (wrong_installment[0], payment_id))

                label(
                    "ANOM-003", "payments", payment_id,
                    "WRONG_INSTALLMENT_ALLOCATION",
                    "Payment references an installment belonging to another loan."
                )

        # 4. Promise amount exceeds case arrears
        promise = conn.execute("""
            SELECT
                p.promise_id,
                cc.arrears
            FROM promises_to_pay p
            JOIN collection_cases cc ON p.case_id = cc.case_id
            LIMIT 1
        """).fetchone()

        if promise:
            promise_id, arrears = promise

            conn.execute("""
                UPDATE promises_to_pay
                SET promised_amount = ?
                WHERE promise_id = ?
            """, (round(arrears + 1000, 2), promise_id))

            label(
                "ANOM-004", "promises_to_pay", promise_id,
                "PROMISE_EXCEEDS_ARREARS",
                "Promised amount exceeds the collection case arrears."
            )

        # 5. Disputed debt incorrectly treated as confirmed
        disputed_case = conn.execute("""
            SELECT case_id
            FROM collection_cases
            WHERE case_status = 'OPEN'
            LIMIT 1
        """).fetchone()

        if disputed_case:
            case_id = disputed_case[0]

            conn.execute("""
                UPDATE collection_cases
                SET issue_type = 'DISPUTED_DEBT_CONFIRMED'
                WHERE case_id = ?
            """, (case_id,))

            label(
                "ANOM-005", "collection_cases", case_id,
                "DISPUTED_DEBT_TREATED_AS_CONFIRMED",
                "Disputed debt is incorrectly represented as confirmed."
            )

        conn.commit()

        total = conn.execute("""
            SELECT COUNT(*) FROM anomaly_labels
        """).fetchone()[0]

        print("Anomaly injection completed.")
        print(f"Labelled anomalies injected: {total}")

        for anomaly_type, count in conn.execute("""
            SELECT anomaly_type, COUNT(*)
            FROM anomaly_labels
            GROUP BY anomaly_type
            ORDER BY anomaly_type
        """):
            print(f"{anomaly_type}: {count}")


if __name__ == "__main__":
    run_anomaly_engine()
