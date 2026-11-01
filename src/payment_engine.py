
import random
import sqlite3
from datetime import date, timedelta

from src.schema import DB_PATH

SEED = 20261022
REFERENCE_DATE = date(2026, 10, 22)


def random_payment_date(due_date):
    days_late = (REFERENCE_DATE - due_date).days

    if days_late <= 0:
        return due_date

    offset = random.randint(0, days_late)
    return due_date + timedelta(days=offset)


def run_payment_engine():
    random.seed(SEED)

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("PRAGMA foreign_keys = ON")

        # Reset previous simulated payments
        conn.execute("DELETE FROM payments")

        conn.execute("""
            UPDATE installments
            SET amount_paid = 0
        """)

        payment_number = 0

        installments = conn.execute("""
            SELECT installment_id, loan_id, due_date, amount_due
            FROM installments
            WHERE due_date < ?
            ORDER BY installment_id
        """, (REFERENCE_DATE.isoformat(),)).fetchall()

        for installment_id, loan_id, due_date_text, amount_due in installments:
            # Simulate different payment behaviours
            outcome = random.random()

            if outcome < 0.35:
                continue

            if outcome < 0.75:
                amount_paid = round(amount_due, 2)
            else:
                amount_paid = round(
                    amount_due * random.uniform(0.20, 0.80), 2
                )

            if amount_paid <= 0:
                continue

            due_date = date.fromisoformat(due_date_text)
            payment_date = random_payment_date(due_date)

            payment_number += 1
            payment_id = f"PMT-2026-{payment_number:06d}"

            conn.execute("""
                INSERT INTO payments (
                    payment_id,
                    loan_id,
                    installment_id,
                    payment_date,
                    amount
                )
                VALUES (?, ?, ?, ?, ?)
            """, (
                payment_id,
                loan_id,
                installment_id,
                payment_date.isoformat(),
                amount_paid
            ))

            conn.execute("""
                UPDATE installments
                SET amount_paid = ?,
                    status = ?
                WHERE installment_id = ?
            """, (
                amount_paid,
                "PAID" if amount_paid >= amount_due else "PARTIAL",
                installment_id
            ))

        # Update remaining installment statuses
        conn.execute("""
            UPDATE installments
            SET status = CASE
                WHEN amount_paid >= amount_due THEN 'PAID'
                WHEN amount_paid > 0 THEN 'PARTIAL'
                WHEN due_date < ? THEN 'OVERDUE'
                ELSE 'UPCOMING'
            END
        """, (REFERENCE_DATE.isoformat(),))

        # Recalculate outstanding loan balances
        conn.execute("""
            UPDATE loans
            SET outstanding_balance = MAX(
                0,
                principal - COALESCE(
                    (
                        SELECT SUM(p.amount)
                        FROM payments p
                        WHERE p.loan_id = loans.loan_id
                    ),
                    0
                )
            )
        """)

        conn.commit()

        total_payments, total_amount = conn.execute("""
            SELECT COUNT(*), COALESCE(SUM(amount), 0)
            FROM payments
        """).fetchone()

        print("Payment engine completed.")
        print(f"Payments generated: {total_payments}")
        print(f"Total payment amount: Rs. {total_amount:,.2f}")


if __name__ == "__main__":
    run_payment_engine()
