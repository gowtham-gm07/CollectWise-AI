
import random
import sqlite3
import calendar
from datetime import date

from faker import Faker

from src.schema import initialize_database, DB_PATH

SEED = 20261022
REFERENCE_DATE = date(2026, 10, 22)

fake = Faker("en_IN")


def add_months(original_date, months):
    month_index = original_date.month - 1 + months
    year = original_date.year + month_index // 12
    month = month_index % 12 + 1

    day = min(
        original_date.day,
        calendar.monthrange(year, month)[1]
    )

    return date(year, month, day)


def generate_base_data(n_loans=500):
    random.seed(SEED)
    Faker.seed(SEED)
    fake.seed_instance(SEED)

    initialize_database()

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("PRAGMA foreign_keys = ON")

        tables = [
            "case_events",
            "contact_attempts",
            "promises_to_pay",
            "payments",
            "delinquency_snapshots",
            "collection_cases",
            "installments",
            "loans",
            "accounts",
            "contact_preferences",
            "customers"
        ]

        for table in tables:
            conn.execute(f"DELETE FROM {table}")

        for i in range(1, n_loans + 1):
            customer_id = f"CUS-2026-{i:06d}"
            account_id = f"ACC-2026-{i:06d}"
            loan_id = f"LOAN-2026-{i:06d}"

            conn.execute("""
                INSERT INTO customers VALUES (?, ?, ?, ?, ?, ?)
            """, (
                customer_id,
                fake.name(),
                fake.email(),
                fake.phone_number(),
                random.choice(["LOW", "MEDIUM", "HIGH"]),
                random.choice([0, 0, 0, 1])
            ))

            issue_date = add_months(REFERENCE_DATE, -12)

            conn.execute("""
                INSERT INTO accounts VALUES (?, ?, ?, ?, ?)
            """, (
                account_id,
                customer_id,
                random.choice(["SAVINGS", "CURRENT", "LOAN"]),
                issue_date.isoformat(),
                "ACTIVE"
            ))

            principal = round(random.uniform(50000, 500000), 2)
            interest_rate = round(random.uniform(8, 18), 2)

            conn.execute("""
                INSERT INTO loans VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                loan_id,
                customer_id,
                principal,
                principal,
                interest_rate,
                "ACTIVE",
                issue_date.isoformat()
            ))

            # Three installments distributed across 12 months.
            # Final installment absorbs rounding differences.
            regular_amount = round(principal / 3, 2)

            for installment_number in range(1, 4):
                installment_id = (
                    f"INS-{loan_id}-{installment_number:03d}"
                )

                due_date = add_months(
                    issue_date,
                    installment_number * 4
                )

                amount_due = (
                    round(principal - regular_amount * 2, 2)
                    if installment_number == 3
                    else regular_amount
                )

                status = (
                    "OVERDUE"
                    if due_date < REFERENCE_DATE
                    else "UPCOMING"
                )

                conn.execute("""
                    INSERT INTO installments
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    installment_id,
                    loan_id,
                    due_date.isoformat(),
                    amount_due,
                    0,
                    status
                ))

            conn.execute("""
                INSERT INTO contact_preferences
                VALUES (?, ?, ?, ?, ?)
            """, (
                customer_id,
                random.choice(["PHONE", "SMS", "EMAIL"]),
                "09:00",
                "18:00",
                random.choice([0, 0, 0, 1])
            ))

        conn.commit()

    print(f"Successfully generated {n_loans} loans.")
    print(f"Installments generated: {n_loans * 3}")
    print("Installment schedule: 3 installments across 12 months.")
    print(f"Database: {DB_PATH}")


if __name__ == "__main__":
    generate_base_data()
