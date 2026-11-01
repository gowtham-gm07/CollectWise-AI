
import random
import sqlite3
import calendar
from datetime import date
from pathlib import Path

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

        # Clear existing records in dependency order
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

            customer_name = fake.name()
            email = fake.email()
            phone = fake.phone_number()

            risk_segment = random.choice(
                ["LOW", "MEDIUM", "HIGH"]
            )

            hardship_flag = random.choice([0, 0, 0, 1])

            conn.execute("""
                INSERT INTO customers VALUES (?, ?, ?, ?, ?, ?)
            """, (
                customer_id,
                customer_name,
                email,
                phone,
                risk_segment,
                hardship_flag
            ))

            opened_date = add_months(REFERENCE_DATE, -12)

            conn.execute("""
                INSERT INTO accounts VALUES (?, ?, ?, ?, ?)
            """, (
                account_id,
                customer_id,
                random.choice(["SAVINGS", "CURRENT", "LOAN"]),
                opened_date.isoformat(),
                "ACTIVE"
            ))

            principal = round(
                random.uniform(50000, 500000), 2
            )

            interest_rate = round(
                random.uniform(8, 18), 2
            )

            issue_date = add_months(
                REFERENCE_DATE,
                -12
            )

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

            monthly_amount = round(principal / 12, 2)

            for installment_number in range(1, 13):
                installment_id = (
                    f"INS-{loan_id}-{installment_number:03d}"
                )

                due_date = add_months(
                    issue_date,
                    installment_number
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
                    monthly_amount,
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
    print(f"Installments generated: {n_loans * 12}")
    print(f"Database: {DB_PATH}")


if __name__ == "__main__":
    generate_base_data()
