# CollectWise-AI
# CollectWise AI

**Intelligent Loan Delinquency & Collections Management Engine**

*Smarter Collections. Responsible Decisions. Complete Transparency.*

## Overview

CollectWise AI is a Python-based loan collections data engine that generates synthetic loan portfolio data, tracks payment and delinquency activity, creates collection cases, manages payment promises, monitors contact compliance, and identifies data-quality anomalies.

The project uses SQLite for storage and exports datasets in CSV, JSON, and SQL formats.

## Core Features

- Synthetic customer, account, loan, and installment generation.
- Payment simulation, including full and partial payments.
- Delinquency tracking using days past due (DPD) and outstanding arrears.
- Collection case creation and priority scoring.
- Promise-to-pay generation and status tracking.
- Contact preference and do-not-contact handling.
- Labelled anomaly injection for validation testing.
- Data validation and export to CSV, JSON, and SQL.
- Automated system tests.

## Technology Stack

- Python
- SQLite
- Pandas
- NumPy
- Faker
- Unittest

## Project Structure

```text
CollectWise-AI/
├── data/
│   ├── raw/
│   ├── processed/
│   └── collectwise.db
├── docs/
├── exports/
├── src/
│   ├── schema.py
│   ├── data_generator.py
│   ├── payment_engine.py
│   ├── delinquency_engine.py
│   ├── priority_engine.py
│   ├── contact_engine.py
│   ├── promise_engine.py
│   ├── anomaly_engine.py
│   ├── validator.py
│   └── exporter.py
├── tests/
│   └── test_system.py
├── main.py
├── requirements.txt
└── README.md
```

## Setup

Create and activate a virtual environment:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
pip install -r requirements.txt
```

## Run the Pipeline

Example: generate a portfolio of 10,000 loans.

```powershell
python main.py --loans 10000
```

The pipeline generates synthetic records, simulates payments, calculates delinquency, creates collection cases, generates promises and contact attempts, injects labelled anomalies, validates the data, and exports the results.

**Note:** Each pipeline run regenerates the database and exports.

## Generated Dataset

The completed 10,000-loan run produced:

| Dataset | Records |
|---|---:|
| Customers | 10,000 |
| Accounts | 10,000 |
| Loans | 10,000 |
| Installments | 120,000 |
| Delinquency snapshots | 10,000 |
| Collection cases | 10,000 |
| Contact attempts | 7,452 |
| Promises to pay | 4,567 |
| Payments | 71,360 |
| Labelled anomalies | 5 |

The generator currently creates 12 monthly installments per loan.

## Validation

The validator checks data relationships and business rules, including:

- Foreign-key integrity.
- Payment-to-installment allocation.
- Installment payment reconciliation.
- Loan balance reconciliation.
- Contact-time restrictions.
- Do-not-contact restrictions.
- Promise amount consistency.
- Disputed-debt handling.

The five injected anomalies are intentional test cases. Validation findings demonstrate detection of inconsistent records; they do not mean the records have been automatically repaired.

See `exports/validation_report.csv` for the generated findings.

## Run Tests

```powershell
python -m unittest discover -s tests -v
```

The current system test suite contains six tests covering record generation, installment relationships, unique loan IDs, anomaly labels, and foreign-key integrity.

## Reproducibility

The synthetic data generator uses a fixed random seed (`20261022`) and a reference date (`2026-10-22`) to support repeatable test runs.

## Data and Ethics

This project uses synthetic data and does not require real customer records. Contact preferences and do-not-contact flags are represented in the generated data and used by the contact-generation workflow.

## Outputs

Generated database and export files are stored in:

- `data/collectwise.db`
- `exports/`

CSV and JSON files are generated for the supported datasets, alongside an SQL database dump and validation report.