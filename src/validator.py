
import sqlite3
import csv
from pathlib import Path

from src.schema import DB_PATH


def run_validation():
    issues = []

    def add_issue(category, record_id, description):
        issues.append({
            "category": category,
            "record_id": record_id,
            "description": description
        })

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("PRAGMA foreign_keys = ON")

        # 1. Foreign key integrity
        fk_errors = conn.execute(
            "PRAGMA foreign_key_check"
        ).fetchall()

        for error in fk_errors:
            add_issue(
                "FOREIGN_KEY",
                str(error[1]),
                f"Foreign key violation in table {error[0]}"
            )

        # 2. Payments allocated to the wrong loan
        rows = conn.execute("""
            SELECT p.payment_id
            FROM payments p
            JOIN installments i
                ON p.installment_id = i.installment_id
            WHERE p.loan_id != i.loan_id
        """).fetchall()

        for (payment_id,) in rows:
            add_issue(
                "WRONG_PAYMENT_ALLOCATION",
                payment_id,
                "Payment loan does not match installment loan."
            )

        # 3. Installment payment reconciliation
        rows = conn.execute("""
            SELECT
                i.installment_id,
                i.amount_paid,
                COALESCE(SUM(p.amount), 0)
            FROM installments i
            LEFT JOIN payments p
                ON i.installment_id = p.installment_id
            GROUP BY i.installment_id
            HAVING ABS(
                i.amount_paid - COALESCE(SUM(p.amount), 0)
            ) > 0.01
        """).fetchall()

        for installment_id, paid, recorded in rows:
            add_issue(
                "INSTALLMENT_RECONCILIATION",
                installment_id,
                f"Recorded paid amount {paid} differs from payments {recorded}."
            )

        # 4. Loan balance reconciliation
        rows = conn.execute("""
            SELECT
                l.loan_id,
                l.outstanding_balance,
                l.principal - COALESCE(SUM(p.amount), 0)
            FROM loans l
            LEFT JOIN payments p ON l.loan_id = p.loan_id
            GROUP BY l.loan_id
            HAVING ABS(
                l.outstanding_balance -
                (l.principal - COALESCE(SUM(p.amount), 0))
            ) > 0.01
        """).fetchall()

        for loan_id, actual, expected in rows:
            add_issue(
                "LOAN_BALANCE_MISMATCH",
                loan_id,
                f"Outstanding balance {actual} differs from expected {expected}."
            )

        # 5. Paid accounts still in collections
        rows = conn.execute("""
            SELECT cc.case_id
            FROM collection_cases cc
            JOIN loans l ON cc.loan_id = l.loan_id
            WHERE l.outstanding_balance <= 0
              AND cc.case_status = 'OPEN'
        """).fetchall()

        for (case_id,) in rows:
            add_issue(
                "PAID_ACCOUNT_IN_COLLECTIONS",
                case_id,
                "Zero-balance loan has an open collection case."
            )

        # 6. Contact outside permitted hours
        rows = conn.execute("""
            SELECT ca.attempt_id
            FROM contact_attempts ca
            JOIN collection_cases cc ON ca.case_id = cc.case_id
            JOIN loans l ON cc.loan_id = l.loan_id
            JOIN contact_preferences cp
                ON l.customer_id = cp.customer_id
            WHERE time(ca.attempted_at) < cp.contact_start
               OR time(ca.attempted_at) > cp.contact_end
        """).fetchall()

        for (attempt_id,) in rows:
            add_issue(
                "CONTACT_OUTSIDE_ALLOWED_WINDOW",
                attempt_id,
                "Contact attempt occurred outside allowed contact hours."
            )

        # 7. Do Not Contact violations
        rows = conn.execute("""
            SELECT ca.attempt_id
            FROM contact_attempts ca
            JOIN collection_cases cc ON ca.case_id = cc.case_id
            JOIN loans l ON cc.loan_id = l.loan_id
            JOIN contact_preferences cp
                ON l.customer_id = cp.customer_id
            WHERE cp.do_not_contact = 1
        """).fetchall()

        for (attempt_id,) in rows:
            add_issue(
                "DO_NOT_CONTACT_VIOLATION",
                attempt_id,
                "Contact attempt exists for a Do Not Contact customer."
            )

        # 8. Promise amount greater than arrears
        rows = conn.execute("""
            SELECT p.promise_id
            FROM promises_to_pay p
            JOIN collection_cases cc ON p.case_id = cc.case_id
            WHERE p.promised_amount > cc.arrears
        """).fetchall()

        for (promise_id,) in rows:
            add_issue(
                "PROMISE_EXCEEDS_ARREARS",
                promise_id,
                "Promised amount exceeds current case arrears."
            )

        # 9. Disputed debt treated as confirmed
        rows = conn.execute("""
            SELECT case_id
            FROM collection_cases
            WHERE issue_type = 'DISPUTED_DEBT_CONFIRMED'
        """).fetchall()

        for (case_id,) in rows:
            add_issue(
                "DISPUTED_DEBT_TREATED_AS_CONFIRMED",
                case_id,
                "Disputed debt is incorrectly treated as confirmed."
            )

        # 10. Check installment date ordering
        rows = conn.execute("""
            SELECT i.installment_id
            FROM installments i
            JOIN loans l ON i.loan_id = l.loan_id
            WHERE i.due_date < l.issue_date
        """).fetchall()

        for (installment_id,) in rows:
            add_issue(
                "INVALID_INSTALLMENT_DATE",
                installment_id,
                "Installment due date is earlier than loan issue date."
            )

        # Save validation results
        output_dir = Path("exports")
        output_dir.mkdir(exist_ok=True)

        report_path = output_dir / "validation_report.csv"

        with open(report_path, "w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(
                file,
                fieldnames=["category", "record_id", "description"]
            )
            writer.writeheader()
            writer.writerows(issues)

        # Compare detected anomalies with injected labels
        expected = conn.execute("""
            SELECT COUNT(*) FROM anomaly_labels
        """).fetchone()[0]

        detected = len(issues)

        print("\n========== COLLECTWISE VALIDATION ==========")
        print(f"Total validation issues: {detected}")
        print(f"Injected anomaly labels: {expected}")

        print("\nIssue breakdown:")

        categories = {}
        for issue in issues:
            categories[issue["category"]] = (
                categories.get(issue["category"], 0) + 1
            )

        for category, count in sorted(categories.items()):
            print(f"{category}: {count}")

        print(f"\nReport saved: {report_path}")
        print("============================================")


if __name__ == "__main__":
    run_validation()
