
import sqlite3
from pathlib import Path

DB_PATH = Path("data/collectwise.db")

SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS customers (
    customer_id TEXT PRIMARY KEY,
    full_name TEXT NOT NULL,
    email TEXT,
    phone TEXT,
    risk_segment TEXT NOT NULL,
    hardship_flag INTEGER DEFAULT 0
);
CREATE TABLE IF NOT EXISTS accounts (
    account_id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL,
    account_type TEXT NOT NULL,
    opened_date TEXT NOT NULL,
    account_status TEXT NOT NULL,
    FOREIGN KEY(customer_id) REFERENCES customers(customer_id)
);
CREATE TABLE IF NOT EXISTS loans (
    loan_id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL,
    principal REAL NOT NULL CHECK(principal >= 0),
    outstanding_balance REAL NOT NULL CHECK(outstanding_balance >= 0),
    interest_rate REAL NOT NULL,
    loan_status TEXT NOT NULL,
    issue_date TEXT NOT NULL,
    FOREIGN KEY(customer_id) REFERENCES customers(customer_id)
);

CREATE TABLE IF NOT EXISTS installments (
    installment_id TEXT PRIMARY KEY,
    loan_id TEXT NOT NULL,
    due_date TEXT NOT NULL,
    amount_due REAL NOT NULL CHECK(amount_due >= 0),
    amount_paid REAL DEFAULT 0 CHECK(amount_paid >= 0),
    status TEXT NOT NULL,
    FOREIGN KEY(loan_id) REFERENCES loans(loan_id)
);

CREATE TABLE IF NOT EXISTS contact_preferences (
    customer_id TEXT PRIMARY KEY,
    preferred_channel TEXT NOT NULL,
    contact_start TEXT NOT NULL,
    contact_end TEXT NOT NULL,
    do_not_contact INTEGER DEFAULT 0,
    FOREIGN KEY(customer_id) REFERENCES customers(customer_id)
);

CREATE TABLE IF NOT EXISTS collection_cases (
    case_id TEXT PRIMARY KEY,
    loan_id TEXT NOT NULL,
    dpd INTEGER NOT NULL,
    arrears REAL NOT NULL,
    priority_score REAL NOT NULL,
    case_status TEXT NOT NULL,
    issue_type TEXT,
    FOREIGN KEY(loan_id) REFERENCES loans(loan_id)
);

CREATE TABLE IF NOT EXISTS contact_attempts (
    attempt_id TEXT PRIMARY KEY,
    case_id TEXT NOT NULL,
    attempted_at TEXT NOT NULL,
    channel TEXT NOT NULL,
    outcome TEXT NOT NULL,
    compliance_status TEXT NOT NULL,
    FOREIGN KEY(case_id) REFERENCES collection_cases(case_id)
);

CREATE TABLE IF NOT EXISTS promises_to_pay (
    promise_id TEXT PRIMARY KEY,
    case_id TEXT NOT NULL,
    promised_amount REAL NOT NULL,
    promised_date TEXT NOT NULL,
    promise_status TEXT NOT NULL,
    FOREIGN KEY(case_id) REFERENCES collection_cases(case_id)
);

CREATE TABLE IF NOT EXISTS payments (
    payment_id TEXT PRIMARY KEY,
    loan_id TEXT NOT NULL,
    installment_id TEXT,
    payment_date TEXT NOT NULL,
    amount REAL NOT NULL CHECK(amount > 0),
    FOREIGN KEY(loan_id) REFERENCES loans(loan_id),
    FOREIGN KEY(installment_id) REFERENCES installments(installment_id)
);

CREATE TABLE IF NOT EXISTS delinquency_snapshots (
    snapshot_id TEXT PRIMARY KEY,
    loan_id TEXT NOT NULL,
    snapshot_date TEXT NOT NULL,
    dpd INTEGER NOT NULL,
    arrears REAL NOT NULL,
    FOREIGN KEY(loan_id) REFERENCES loans(loan_id)
);

CREATE TABLE IF NOT EXISTS case_events (
    event_id TEXT PRIMARY KEY,
    case_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    event_time TEXT NOT NULL,
    description TEXT NOT NULL,
    FOREIGN KEY(case_id) REFERENCES collection_cases(case_id)
);
"""

def initialize_database():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as connection:
        connection.executescript(SCHEMA)
    print(f"Database initialized: {DB_PATH}")
